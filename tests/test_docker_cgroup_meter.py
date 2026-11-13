import tempfile
import unittest
from pathlib import Path

from xparallel.docker_cgroup_meter import DockerCgroupV2Meter


class DockerCgroupV2MeterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "cgroup"
        self.group = self.root / "docker" / ("a" * 64)
        self.group.mkdir(parents=True)
        self.proc = Path(self.tmp.name) / "proc"
        (self.proc / "123").mkdir(parents=True)
        (self.proc / "123" / "cgroup").write_text(
            "0::/docker/" + "a" * 64 + "\n", encoding="ascii"
        )
        (self.group / "cpu.stat").write_text("usage_usec 250000\nuser_usec 100000\n")
        for name, value in {
            "memory.current": "1048576", "memory.peak": "2097152",
            "pids.current": "2", "pids.peak": "4",
        }.items():
            (self.group / name).write_text(value)
        self.clock = [10.0]
        self.meter = DockerCgroupV2Meter(
            cgroup_root=str(self.root), proc_root=str(self.proc),
            inspect=lambda cid: 123, monotonic=lambda: self.clock[0],
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_measures_cgroup_cpu_memory_pids_and_wall_time(self):
        self.meter.sample("a" * 64)
        self.clock[0] = 12.5
        result = self.meter.finish("a" * 64, output_bytes=77)
        self.assertEqual(result["wall_ms"], 2500)
        self.assertEqual(result["cpu_ms"], 250)
        self.assertEqual(result["memory_peak_mb"], 2)
        self.assertEqual(result["pids_peak"], 4)
        self.assertEqual(result["output_bytes"], 77)
        self.assertEqual(result["measurement_source"], "linux-cgroup-v2")

    def test_refuses_missing_live_sample(self):
        with self.assertRaisesRegex(RuntimeError, "live_cgroup_sample_required"):
            self.meter.finish("a" * 64, output_bytes=0)

    def test_rejects_invalid_container_id(self):
        with self.assertRaisesRegex(ValueError, "invalid_docker_container_id"):
            self.meter.sample("../escape")

    def test_rejects_cgroup_path_escape(self):
        (self.proc / "123" / "cgroup").write_text("0::/../../etc\n")
        with self.assertRaisesRegex(RuntimeError, "outside_host_root"):
            self.meter.sample("a" * 64)

    def test_requires_unified_cgroup_v2(self):
        (self.proc / "123" / "cgroup").write_text("2:cpu:/docker\n")
        with self.assertRaisesRegex(RuntimeError, "unified_hierarchy_required"):
            self.meter.sample("a" * 64)


if __name__ == "__main__":
    unittest.main()
