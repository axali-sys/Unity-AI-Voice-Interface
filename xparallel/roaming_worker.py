"""Safe outbound XParallel roaming worker.

The worker polls XParallel over HTTPS and executes only registered task handlers.
It never evaluates arbitrary code, invokes a shell, or downloads executable tasks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable


MAX_RESPONSE_BYTES = 128_000
DEFAULT_CAPABILITIES = ("echo", "text.uppercase")


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_write_token(path: Path, token: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(str(path), flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(token)
            stream.write("\n")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


class WorkerError(RuntimeError):
    pass


class XParallelWorker:
    """A small polling worker authenticated by its per-runtime bearer token."""

    def __init__(
        self,
        api_url: str,
        runtime_id: str,
        name: str,
        advertised_url: str,
        capabilities=None,
        token_file: str | os.PathLike = ".xparallel-worker-token",
        owner_token: str | None = None,
        poll_seconds: float = 5,
        heartbeat_seconds: float = 60,
        timeout_seconds: float = 20,
        handlers: dict[str, Callable[[dict], dict]] | None = None,
    ):
        self.api_url = api_url.rstrip("/")
        self.runtime_id = runtime_id
        self.name = name
        self.advertised_url = advertised_url
        self.capabilities = tuple(capabilities or DEFAULT_CAPABILITIES)
        self.token_file = Path(token_file)
        self.owner_token = owner_token
        self.poll_seconds = max(1.0, float(poll_seconds))
        self.heartbeat_seconds = max(10.0, float(heartbeat_seconds))
        self.timeout_seconds = max(1.0, float(timeout_seconds))
        self.handlers = handlers or {
            "echo": self._echo,
            "text.uppercase": self._uppercase,
        }
        self.runtime_token: str | None = None
        self._last_heartbeat = 0.0
        self._stop = False

        if not self.api_url.startswith("https://") and not self.api_url.startswith("http://127.0.0.1") and not self.api_url.startswith("http://localhost"):
            raise ValueError("xparallel_api_url_must_use_https")
        if not self.runtime_id or len(self.runtime_id) > 80:
            raise ValueError("runtime_id_invalid")
        if not self.advertised_url:
            raise ValueError("worker_advertised_url_required")
        if not self.capabilities or any(cap not in self.handlers for cap in self.capabilities):
            raise ValueError("worker_capabilities_must_match_safe_handlers")

    @staticmethod
    def _echo(payload: dict) -> dict:
        return {"echo": payload}

    @staticmethod
    def _uppercase(payload: dict) -> dict:
        value = payload.get("text")
        if not isinstance(value, str):
            raise ValueError("text.uppercase_requires_text")
        if len(value) > 16000:
            raise ValueError("text.uppercase_input_too_large")
        return {"text": value.upper()}

    def _request(self, path: str, payload: dict, token: str | None = None) -> dict:
        body = _canonical(payload)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            self.api_url + path, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise WorkerError("xparallel_response_too_large")
                parsed = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(parsed, dict):
                    raise WorkerError("xparallel_response_invalid")
                return parsed
        except urllib.error.HTTPError as exc:
            detail = exc.read(2048).decode("utf-8", "replace")
            raise WorkerError(f"xparallel_http_{exc.code}:{detail}") from exc
        except urllib.error.URLError as exc:
            raise WorkerError("xparallel_connection_failed") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorkerError("xparallel_response_invalid") from exc

    def register(self) -> None:
        if self.token_file.exists():
            token = self.token_file.read_text(encoding="utf-8").strip()
            if not token:
                raise WorkerError("worker_token_file_empty")
            self.runtime_token = token
            self.heartbeat(force=True)
            return
        if not self.owner_token:
            raise WorkerError("XP_TOKEN_required_for_first_registration")
        result = self._request("/roaming/register", {
            "runtime_id": self.runtime_id,
            "name": self.name,
            "base_url": self.advertised_url,
            "capabilities": list(self.capabilities),
        }, self.owner_token)
        token = result.get("runtime_token")
        if not isinstance(token, str) or len(token) < 32:
            raise WorkerError("runtime_registration_did_not_return_token")
        _safe_write_token(self.token_file, token)
        self.runtime_token = token
        self._last_heartbeat = time.monotonic()

    def heartbeat(self, force: bool = False) -> None:
        if not self.runtime_token:
            raise WorkerError("worker_not_registered")
        now = time.monotonic()
        if force or now - self._last_heartbeat >= self.heartbeat_seconds:
            self._request("/roaming/heartbeat", {"runtime_id": self.runtime_id}, self.runtime_token)
            self._last_heartbeat = now

    def execute(self, task: dict) -> dict:
        task_type = task.get("task_type")
        payload = task.get("payload")
        if task_type not in self.capabilities or task_type not in self.handlers:
            raise ValueError("task_type_not_allowlisted")
        if not isinstance(payload, dict):
            raise ValueError("task_payload_must_be_object")
        input_digest = _sha256(payload)
        output = self.handlers[task_type](payload)
        if not isinstance(output, dict):
            raise ValueError("task_handler_result_must_be_object")
        return {
            "worker_id": self.runtime_id,
            "task_type": task_type,
            "input_sha256": input_digest,
            "output": output,
            "output_sha256": _sha256(output),
            "verified": True,
            "verification": "sha256_of_canonical_json_input_and_output",
            "executed_at": time.time(),
        }

    def run_once(self) -> bool:
        self.heartbeat()
        claim = self._request(
            "/roaming/tasks/claim",
            {"runtime_id": self.runtime_id, "lease_seconds": 120},
            self.runtime_token,
        )
        task = claim.get("task")
        if not task:
            return False
        task_id = task.get("task_id")
        try:
            result = self.execute(task)
            failed = False
        except Exception as exc:
            result = {
                "worker_id": self.runtime_id,
                "task_type": task.get("task_type"),
                "error": str(exc)[:500],
                "verified": False,
                "executed_at": time.time(),
            }
            failed = True
        self._request("/roaming/tasks/complete", {
            "runtime_id": self.runtime_id,
            "task_id": task_id,
            "result": result,
            "failed": failed,
        }, self.runtime_token)
        return True

    def stop(self, *_args) -> None:
        self._stop = True

    def run_forever(self) -> None:
        if not self.runtime_token:
            self.register()
        while not self._stop:
            try:
                worked = self.run_once()
            except WorkerError:
                # A transient outage must not terminate the worker process.
                worked = False
            if not worked:
                time.sleep(self.poll_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description="XParallel safe roaming worker")
    parser.add_argument("--api-url", default=os.getenv("XP_API_URL", ""))
    parser.add_argument("--runtime-id", default=os.getenv("XP_WORKER_ID", ""))
    parser.add_argument("--name", default=os.getenv("XP_WORKER_NAME", "XParallel Worker"))
    parser.add_argument("--advertised-url", default=os.getenv("XP_WORKER_PUBLIC_URL", ""))
    parser.add_argument("--token-file", default=os.getenv("XP_WORKER_TOKEN_FILE", ".xparallel-worker-token"))
    args = parser.parse_args()
    if not args.api_url or not args.runtime_id or not args.advertised_url:
        parser.error("XP_API_URL, XP_WORKER_ID and XP_WORKER_PUBLIC_URL are required")
    worker = XParallelWorker(
        args.api_url, args.runtime_id, args.name, args.advertised_url,
        token_file=args.token_file, owner_token=os.getenv("XP_TOKEN"),
        poll_seconds=float(os.getenv("XP_WORKER_POLL_SECONDS", "5")),
        heartbeat_seconds=float(os.getenv("XP_WORKER_HEARTBEAT_SECONDS", "60")),
    )
    signal.signal(signal.SIGINT, worker.stop)
    signal.signal(signal.SIGTERM, worker.stop)
    worker.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
