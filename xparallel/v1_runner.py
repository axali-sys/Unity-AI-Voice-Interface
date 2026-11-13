"""Resource-limited Docker runner for untrusted project tests.

The runner is intentionally unavailable unless its image is pinned by digest.
It executes only in a disposable workspace and never mounts host credentials.
It is a defense-in-depth development sandbox, not a substitute for a hardened
multi-tenant microVM or independent security review.
"""
import base64
import binascii
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

IMAGE = os.getenv("XP_RUNNER_IMAGE", "").strip()
TIMEOUT = int(os.getenv("XP_RUNNER_TIMEOUT", "60"))
MAX_FILES = int(os.getenv("XP_RUNNER_MAX_FILES", "200"))
MAX_FILE_BYTES = int(os.getenv("XP_RUNNER_MAX_FILE_BYTES", str(256 * 1024)))
MAX_TOTAL_BYTES = int(os.getenv("XP_RUNNER_MAX_TOTAL_BYTES", str(10 * 1024 * 1024)))
MEMORY = os.getenv("XP_RUNNER_MEMORY", "512m")
CPUS = os.getenv("XP_RUNNER_CPUS", "1.0")
PIDS = os.getenv("XP_RUNNER_PIDS", "128")
NONROOT_UID = 65532
NONROOT_GID = 65532


def _valid_limits():
    return (
        1 <= TIMEOUT <= 600
        and 1 <= MAX_FILES <= 1000
        and 1 <= MAX_FILE_BYTES <= 2 * 1024 * 1024
        and 1 <= MAX_TOTAL_BYTES <= 50 * 1024 * 1024
        and MEMORY.endswith(("m", "g"))
        and CPUS.replace(".", "", 1).isdigit()
        and PIDS.isdigit()
        and 1 <= int(PIDS) <= 1024
    )


def _image_is_pinned(image):
    if not isinstance(image, str) or "@sha256:" not in image:
        return False
    digest = image.rsplit("@sha256:", 1)[-1]
    return len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest.lower())


def available():
    if not _valid_limits() or not _image_is_pinned(IMAGE) or shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(
            ["docker", "info"], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=5, check=False,
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _write_workspace(root, files):
    if not isinstance(files, dict) or not files:
        raise ValueError("files_must_be_non_empty_object")
    if len(files) > MAX_FILES:
        raise ValueError("too_many_files")
    total = 0
    for name, encoded in files.items():
        if not isinstance(name, str) or not name or "\x00" in name or "\\" in name:
            raise ValueError("invalid_file_path")
        path = Path(name)
        if path.is_absolute() or any(part in ("..", ".") for part in path.parts):
            raise ValueError("unsafe_file_path")
        if not isinstance(encoded, str) or len(encoded) > ((MAX_FILE_BYTES + 2) // 3) * 4:
            raise ValueError("invalid_or_oversized_file_content")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("invalid_base64_file_content") from exc
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError("file_exceeds_size_limit")
        total += len(raw)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("workspace_exceeds_size_limit")
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        os.chmod(target, 0o666)
    # The unprivileged container UID needs access to this disposable tree.
    os.chmod(root, 0o755)
    for directory in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts)):
        os.chmod(directory, 0o777)


def _docker_command(root, test_command):
    return [
        "docker", "run", "--rm",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--security-opt=seccomp=default",
        "--user", f"{NONROOT_UID}:{NONROOT_GID}",
        "--ipc=private",
        "--memory", MEMORY,
        "--memory-swap", MEMORY,
        "--cpus", CPUS,
        "--pids-limit", PIDS,
        "--ulimit", "nofile=256:256",
        "--ulimit", "fsize=10485760:10485760",
        "--tmpfs", f"/tmp:rw,noexec,nosuid,nodev,size=64m,uid={NONROOT_UID},gid={NONROOT_GID}",
        "--env", "HOME=/tmp",
        "--mount", f"type=bind,src={root},dst=/workspace,rw",
        "--workdir", "/workspace",
        IMAGE, "sh", "-lc", test_command,
    ]


def run_project(intent):
    started = datetime.now(timezone.utc).isoformat()
    if not isinstance(intent, dict):
        return {"environment": "docker", "status": "failed", "error": "invalid_intent"}
    test_command = intent.get("test_command", "python -m unittest discover -v")
    if not isinstance(test_command, str) or not test_command.strip() or len(test_command) > 1000:
        return {"environment": "docker", "status": "failed", "error": "invalid_test_command"}
    if not _valid_limits():
        return {"environment": "docker", "status": "blocked", "error": "invalid_sandbox_limits"}
    if not _image_is_pinned(IMAGE):
        return {"environment": "docker", "status": "blocked", "error": "runner_image_digest_not_pinned"}
    if shutil.which("docker") is None:
        return {"environment": "docker", "status": "blocked", "error": "docker_unavailable"}
    if not available():
        return {"environment": "docker", "status": "blocked", "error": "docker_daemon_unavailable"}
    with tempfile.TemporaryDirectory(prefix="xparallel-sandbox-") as tmp:
        root = Path(tmp)
        try:
            _write_workspace(root, intent.get("files"))
        except (ValueError, OSError) as exc:
            return {"environment": "docker", "status": "failed", "error": str(exc)}
        try:
            completed = subprocess.run(
                _docker_command(root, test_command),
                capture_output=True, text=True, timeout=TIMEOUT, check=False,
                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
            )
        except subprocess.TimeoutExpired:
            return {"environment": "docker", "status": "failed", "error": "test_timeout", "timeout_seconds": TIMEOUT}
        except OSError:
            return {"environment": "docker", "status": "failed", "error": "docker_execution_failed"}
        return {
            "environment": "docker",
            "image": IMAGE,
            "started_at": started,
            "status": "success" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "stdout": completed.stdout[-10000:],
            "stderr": completed.stderr[-10000:],
            "test_command": test_command,
            "isolation": {
                "network": "none", "root_filesystem": "read-only",
                "capabilities": "dropped-all", "non_root_uid": NONROOT_UID,
                "no_new_privileges": True, "seccomp": "default",
                "memory": MEMORY, "memory_swap": MEMORY, "cpus": CPUS,
                "pids_limit": PIDS, "ipc": "private",
                "workspace": "disposable-temporary-bind-mount",
                "host_credentials_mounted": False,
            },
        }
