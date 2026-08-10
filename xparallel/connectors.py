"""Safe external information connectors for XParallel v0.4.

Only explicitly supplied HTTPS URLs are fetched. This is a testnet connector,
not unrestricted internet access.
"""
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_BYTES = 200_000
TIMEOUT = 10


def fetch_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Only valid HTTPS URLs are allowed")
    req = Request(url, headers={"User-Agent": "XParallel-Testnet/0.4"})
    with urlopen(req, timeout=TIMEOUT) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("External response exceeds testnet size limit")
        content_type = response.headers.get("Content-Type", "")
    text = raw.decode("utf-8", errors="replace")
    return {
        "url": url,
        "content_type": content_type,
        "bytes": len(raw),
        "content": text,
    }


def connector_result(url: str) -> dict:
    try:
        return {"status": "ok", "source": fetch_url(url)}
    except Exception as exc:
        return {"status": "error", "url": url, "error": str(exc)}
