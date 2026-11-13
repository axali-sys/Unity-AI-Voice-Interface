"""Linux cgroup v2 resource meter for a running Docker execution container.

The caller must invoke sample() while the container is alive and finish() after
the runner exits but before removing the container. This meter refuses cgroup
v1, missing samples, inaccessible host proc/cgroup data, and malformed metrics.
"""
from __future__ import annotations

import math
import re
import subprocess
import time
from pathlib import Path
from typing import Callable


class DockerCgroupV2Meter:
    def __init__(
        self, *, cgroup_root: str = "/sys/fs/cgroup",
        proc_root: str = "/proc",
        inspect: Callable[[str], int] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self.root = Path(cgroup_root).resolve()
        self.proc = Path(proc_root)
        self._inspect = inspect or self._docker_pid
        self._clock = monotonic
        self._started = self._clock()
        self._cgroup: Path | None = None
        self._last_cpu_usec: int | None = None
        self._samples = 0

    @staticmethod
    def _docker_pid(container_id: str) -> int:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Pid}}", container_id],
            capture_output=True, text=True, timeout=3, check=True,
        )
        value = result.stdout.strip()
        if not value.isdigit() or int(value) <= 0:
            raise RuntimeError("docker_container_pid_unavailable")
        return int(value)

    def _resolve_cgroup(self, container_id: str) -> Path:
        if not isinstance(container_id, str) or not re.fullmatch(r"[0-9a-f]{12,64}", container_id):
            raise ValueError("invalid_docker_container_id")
        pid = self._inspect(container_id)
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            raise RuntimeError("docker_container_pid_unavailable")
        lines = (self.proc / str(pid) / "cgroup").read_text(encoding="ascii").splitlines()
        unified = [line.split(":", 2)[2] for line in lines if line.startswith("0::")]
        if len(unified) != 1 or not unified[0].startswith("/"):
            raise RuntimeError("cgroup_v2_unified_hierarchy_required")
        candidate = (self.root / unified[0].lstrip("/")).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise RuntimeError("container_cgroup_path_outside_host_root")
        if not (candidate / "cpu.stat").is_file():
            raise RuntimeError("container_cgroup_v2_metrics_unavailable")
        self._cgroup = candidate
        return candidate

    @staticmethod
    def _read_kv(path: Path) -> dict[str, int]:
        values: dict[str, int] = {}
        for line in path.read_text(encoding="ascii").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                values[parts[0]] = int(parts[1])
        return values

    def sample(self, container_id: str) -> None:
        group = self._cgroup or self._resolve_cgroup(container_id)
        cpu = self._read_kv(group / "cpu.stat")
        if "usage_usec" not in cpu:
            raise RuntimeError("cgroup_cpu_usage_unavailable")
        self._read_positive(group / "memory.current")
        self._read_positive(group / "memory.peak")
        self._read_positive(group / "pids.current")
        self._read_positive(group / "pids.peak")
        self._last_cpu_usec = cpu["usage_usec"]
        self._samples += 1

    @staticmethod
    def _read_positive(path: Path) -> int:
        value = path.read_text(encoding="ascii").strip()
        if not value.isdigit():
            raise RuntimeError(f"invalid_cgroup_metric:{path.name}")
        return int(value)

    def finish(self, container_id: str, *, output_bytes: int) -> dict[str, int | str]:
        if self._cgroup is None:
            self._resolve_cgroup(container_id)
        if self._samples < 1:
            raise RuntimeError("live_cgroup_sample_required")
        group = self._cgroup
        cpu = self._read_kv(group / "cpu.stat")
        if "usage_usec" not in cpu:
            raise RuntimeError("cgroup_cpu_usage_unavailable")
        memory_peak = self._read_positive(group / "memory.peak")
        pids_peak = self._read_positive(group / "pids.peak")
        elapsed = self._clock() - self._started
        if not math.isfinite(elapsed) or elapsed < 0:
            raise RuntimeError("invalid_execution_wall_clock")
        if not isinstance(output_bytes, int) or isinstance(output_bytes, bool) or output_bytes < 0:
            raise ValueError("invalid_execution_output_bytes")
        return {
            "wall_ms": int(elapsed * 1000),
            "cpu_ms": int(cpu["usage_usec"] // 1000),
            "memory_peak_mb": (memory_peak + 1048575) // 1048576,
            "output_bytes": output_bytes,
            "pids_peak": pids_peak,
            "measurement_source": "linux-cgroup-v2",
            "sample_count": self._samples,
        }
