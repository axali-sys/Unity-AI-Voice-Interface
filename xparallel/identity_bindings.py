"""SQLite registry for proposed identity endpoint bindings.

Bindings remain unverified until an external proof-of-control verifier is configured.
This module deliberately performs no outbound network requests.
"""
from __future__ import annotations
import json
import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

DB_PATH = os.getenv("XP_IDENTITY_DB", ".xparallel/identity_bindings.db")
IDENTITY_KEYS = {"oneai.core", "xparallel.verse"}
ALLOWED_STATES = {"endpoint_unverified", "endpoint_verified", "stale", "revoked"}


def _now():
    return datetime.now(timezone.utc)


def _connect():
    if DB_PATH != ":memory:":
        Path(DB_PATH).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS identity_bindings (
        binding_id TEXT PRIMARY KEY, identity_key TEXT NOT NULL, endpoint_url TEXT NOT NULL,
        owner_id TEXT NOT NULL, state TEXT NOT NULL, challenge TEXT NOT NULL,
        created_at TEXT NOT NULL, expires_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        revoked_at TEXT, metadata_json TEXT NOT NULL
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_identity_bindings_key ON identity_bindings(identity_key, created_at DESC)")
    conn.commit()
    return conn


def _validate_url(value):
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("endpoint_must_be_https_without_credentials")
    if parsed.fragment or len(url) > 2048:
        raise ValueError("invalid_endpoint_url")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("local_endpoint_not_allowed")
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host) or ":" in host:
        raise ValueError("ip_literal_endpoint_not_allowed")
    return url


def _row(row):
    item = dict(row)
    item["metadata"] = json.loads(item.pop("metadata_json"))
    item.pop("challenge", None)
    return item


def create_binding(identity_key, endpoint_url, owner_id, ttl_days=30, metadata=None):
    key, owner = str(identity_key or "").strip(), str(owner_id or "").strip()
    if key not in IDENTITY_KEYS:
        raise ValueError("unknown_identity_key")
    if not owner or len(owner) > 200:
        raise ValueError("owner_id_required")
    url = _validate_url(endpoint_url)
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("metadata_must_be_object")
    try:
        ttl = int(ttl_days)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_ttl_days") from exc
    if not 1 <= ttl <= 90:
        raise ValueError("ttl_days_must_be_1_to_90")
    now = _now()
    binding = {
        "binding_id": "ib_" + uuid.uuid4().hex,
        "identity_key": key,
        "endpoint_url": url,
        "owner_id": owner,
        "state": "endpoint_unverified",
        "challenge": secrets.token_urlsafe(32),
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=ttl)).isoformat(),
        "updated_at": now.isoformat(),
        "revoked_at": None,
        "metadata_json": json.dumps(metadata or {}, sort_keys=True),
    }
    with _connect() as conn:
        conn.execute("INSERT INTO identity_bindings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     tuple(binding.values()))
    result = _row({**binding, "metadata_json": binding["metadata_json"]})
    result["verification_challenge"] = binding["challenge"]
    result["verification_instructions"] = "Publish this exact challenge at /.well-known/xparallel-identity.json; state remains unverified until an approved verifier confirms endpoint control."
    return result


def list_bindings(identity_key=None, owner_id=None):
    query, args = "SELECT * FROM identity_bindings WHERE 1=1", []
    if identity_key:
        query += " AND identity_key=?"; args.append(str(identity_key))
    if owner_id:
        query += " AND owner_id=?"; args.append(str(owner_id))
    query += " ORDER BY created_at DESC LIMIT 200"
    with _connect() as conn:
        rows = conn.execute(query, args).fetchall()
    now = _now()
    results = []
    for row in rows:
        item = _row(row)
        if item["state"] == "endpoint_verified" and datetime.fromisoformat(item["expires_at"]) <= now:
            item["state"] = "stale"
        results.append(item)
    return results


def revoke_binding(binding_id, owner_id):
    now = _now().isoformat()
    with _connect() as conn:
        cur = conn.execute("""UPDATE identity_bindings SET state='revoked', revoked_at=?, updated_at=?
                              WHERE binding_id=? AND owner_id=? AND state!='revoked'""",
                           (now, now, str(binding_id), str(owner_id)))
        row = conn.execute("SELECT * FROM identity_bindings WHERE binding_id=? AND owner_id=?",
                           (str(binding_id), str(owner_id))).fetchone()
    if row is None:
        return None
    item = _row(row)
    item["revocation_changed"] = cur.rowcount == 1
    return item
