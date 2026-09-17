import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xparallel.v1_runner import _write_workspace, run_project


class V1RunnerTests(unittest.TestCase):
    def test_workspace_rejects_parent_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                _write_workspace(Path(tmp), {"../escape.txt": base64.b64encode(b"x").decode()})

    def test_workspace_writes_base64_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_workspace(Path(tmp), {"hello.txt": base64.b64encode(b"hello").decode()})
            self.assertEqual((Path(tmp) / "hello.txt").read_bytes(), b"hello")

    @patch("xparallel.v1_runner.available", return_value=False)
    def test_execution_blocks_without_docker(self, _available):
        result = run_project({"files": {"hello.py": base64.b64encode(b"print('ok')").decode()}})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error"], "docker_unavailable")


if __name__ == "__main__":
    unittest.main()
