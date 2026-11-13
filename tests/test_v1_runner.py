import base64
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from xparallel import v1_runner


class HardenedRunnerTests(unittest.TestCase):
    def encoded(self, value=b"print('ok')"):
        return base64.b64encode(value).decode()

    def test_workspace_rejects_parent_escape_and_backslash_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in ("../escape.txt", "folder/../../escape", "folder\\escape"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    v1_runner._write_workspace(Path(tmp), {path: self.encoded()})

    def test_workspace_rejects_invalid_base64_and_oversized_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                v1_runner._write_workspace(Path(tmp), {"bad.txt": "not base64!"})

    def test_workspace_enforces_total_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(v1_runner, "MAX_TOTAL_BYTES", 4):
                with self.assertRaisesRegex(ValueError, "workspace_exceeds_size_limit"):
                    v1_runner._write_workspace(Path(tmp), {"a": self.encoded(b"123"), "b": self.encoded(b"456")})

    def test_workspace_files_are_writable_by_non_root_container_uid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()
            v1_runner._write_workspace(root, {"src/main.py": self.encoded()})
            self.assertEqual(root.stat().st_mode & 0o777, 0o755)
            self.assertEqual((root / "src").stat().st_mode & 0o777, 0o777)
            self.assertEqual((root / "src/main.py").stat().st_mode & 0o777, 0o666)

    def test_image_must_be_pinned_to_sha256_digest(self):
        self.assertFalse(v1_runner._image_is_pinned("python:3.12-alpine"))
        self.assertFalse(v1_runner._image_is_pinned("image@sha256:bad"))
        self.assertTrue(v1_runner._image_is_pinned("image@sha256:" + "a" * 64))

    def test_docker_command_contains_isolation_controls(self):
        with patch.object(v1_runner, "IMAGE", "image@sha256:" + "a" * 64):
            with tempfile.TemporaryDirectory() as tmp:
                args = v1_runner._docker_command(Path(tmp), "python -m unittest")
        joined = " ".join(args)
        for expected in ("--pull=never", "--init", "--network=none", "--read-only", "--cap-drop=ALL",
                         "--security-opt=no-new-privileges", "--security-opt=seccomp=default",
                         "--user 65532:65532", "--ipc=private", "--pids-limit 128",
                         "--memory-swap 512m", "--workdir /workspace"):
            self.assertIn(expected, joined)
        self.assertNotIn("/var/run/docker.sock", joined)

    def test_resource_limits_reject_unbounded_or_malformed_values(self):
        invalid = [
            {"MEMORY": "999999g"}, {"MEMORY": "0m"}, {"MEMORY": "64mb"},
            {"CPUS": "999"}, {"CPUS": "nan"}, {"CPUS": "0"},
            {"PIDS": "0"}, {"PIDS": "many"}, {"TIMEOUT": 601},
            {"MAX_TOTAL_BYTES": 0},
        ]
        for values in invalid:
            with self.subTest(values=values):
                with patch.multiple(v1_runner, **values):
                    self.assertFalse(v1_runner._valid_limits())

    def test_malformed_integer_environment_does_not_crash_module_configuration(self):
        with patch.object(v1_runner, "TIMEOUT", -1):
            self.assertFalse(v1_runner._valid_limits())

    def test_bounded_runner_caps_stdout_and_stderr_while_draining(self):
        script = "import sys; sys.stdout.write('A' * 500000); sys.stderr.write('B' * 500000)"
        result = v1_runner._run_bounded(
            [sys.executable, "-c", script], timeout=10, env=os.environ.copy(), output_limit=4096
        )
        self.assertEqual(len(result["stdout"]), 4096)
        self.assertEqual(len(result["stderr"]), 4096)
        self.assertTrue(result["output_truncated"]["stdout"])
        self.assertTrue(result["output_truncated"]["stderr"])

    def test_bounded_runner_kills_timed_out_process_group(self):
        with self.assertRaises(v1_runner.subprocess.TimeoutExpired):
            v1_runner._run_bounded(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                timeout=0.1, env=os.environ.copy(), output_limit=1024,
            )

    def test_run_blocks_when_image_is_not_digest_pinned(self):
        with patch.object(v1_runner, "IMAGE", "python:3.12-alpine"):
            result = v1_runner.run_project({"files": {"main.py": self.encoded()}})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error"], "runner_image_digest_not_pinned")

    def test_run_blocks_when_docker_is_unavailable(self):
        with patch.object(v1_runner, "IMAGE", "image@sha256:" + "a" * 64), \
             patch("xparallel.v1_runner.shutil.which", return_value=None):
            result = v1_runner.run_project({"files": {"main.py": self.encoded()}}, approved_limits={"timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000, "pids": 32, "output_bytes": 4096}, expected_image_digest="a" * 64)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error"], "docker_unavailable")

    def test_invalid_command_is_rejected(self):
        result = v1_runner.run_project({"files": {"main.py": self.encoded()}, "test_command": " "})
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"], "invalid_test_command")

    def test_successful_execution_reports_controls_and_truncates_output(self):
        image = "image@sha256:" + "a" * 64
        completed = {
            "returncode": 0, "stdout": "x" * 10000, "stderr": "ok",
            "output_truncated": {"stdout": True, "stderr": False},
        }
        with patch.object(v1_runner, "IMAGE", image), \
             patch.object(v1_runner.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(v1_runner, "available", return_value=True), \
             patch.object(v1_runner, "_run_bounded", return_value=completed) as run:
            result = v1_runner.run_project({"files": {"main.py": self.encoded()}}, approved_limits={"timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000, "pids": 32, "output_bytes": 4096}, expected_image_digest="a" * 64)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["stdout"]), 10000)
        self.assertTrue(result["output_truncated"]["stdout"])
        self.assertTrue(result["isolation"]["host_credentials_mounted"] is False)
        args = run.call_args.args[0]
        self.assertIn("--network=none", args)
        self.assertIn("--user", args)


if __name__ == "__main__":
    unittest.main()
