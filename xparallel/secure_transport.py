"""Encrypted XParallel transport packets and bounded reliable-delivery outbox."""
from __future__ import annotations
import base64, json, secrets, sqlite3, threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_LOCK = threading.RLock()
_VERSION = "1.0"
_MAX_PACKET = 512_000

def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise ValueError(f"invalid_{field}")
    return value

def _key(value: Any) -> bytes:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError("recipient_key_must_be_256_bit_bytes")
    return value

def _headers(workspace: str, recipient: str, key_id: str) -> dict[str, str]:
    return {"version": _VERSION, "workspace_id": workspace, "recipient_entity_id": recipient, "recipient_key_id": key_id}

class EncryptedEnvelopeCodec:
    """AES-256-GCM wrapper for an already-signed entity message envelope."""
    @staticmethod
    def seal(envelope: dict[str, Any], *, recipient_key: bytes, recipient_key_id: str) -> dict[str, Any]:
        if not isinstance(envelope, dict):
            raise ValueError("invalid_signed_envelope")
        workspace = _id(envelope.get("workspace_id"), "workspace_id")
        recipient = _id(envelope.get("recipient_entity_id"), "recipient_entity_id")
        key_id, key = _id(recipient_key_id, "recipient_key_id"), _key(recipient_key)
        headers, nonce = _headers(workspace, recipient, key_id), secrets.token_bytes(12)
        ciphertext = AESGCM(key).encrypt(nonce, _canonical(envelope), _canonical(headers))
        packet = {**headers, "nonce_b64": base64.b64encode(nonce).decode("ascii"),
                  "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii")}
        if len(_canonical(packet)) > _MAX_PACKET:
            raise ValueError("encrypted_packet_too_large")
        return packet

    @staticmethod
    def open(packet: dict[str, Any], *, recipient_key: bytes, expected_workspace_id: str,
             expected_recipient_entity_id: str, expected_key_id: str) -> dict[str, Any]:
        required = {"version","workspace_id","recipient_entity_id","recipient_key_id","nonce_b64","ciphertext_b64"}
        if not isinstance(packet, dict) or set(packet) != required:
            raise ValueError("invalid_encrypted_packet")
        if packet["version"] != _VERSION:
            raise ValueError("unsupported_transport_version")
        workspace, recipient, key_id = (_id(expected_workspace_id,"expected_workspace_id"),
            _id(expected_recipient_entity_id,"expected_recipient_entity_id"), _id(expected_key_id,"expected_key_id"))
        if (packet["workspace_id"],packet["recipient_entity_id"],packet["recipient_key_id"]) != (workspace,recipient,key_id):
            raise ValueError("encrypted_packet_recipient_mismatch")
        if len(_canonical(packet)) > _MAX_PACKET:
            raise ValueError("encrypted_packet_too_large")
        try:
            nonce = base64.b64decode(packet["nonce_b64"], validate=True)
            ciphertext = base64.b64decode(packet["ciphertext_b64"], validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid_encrypted_packet_encoding") from exc
        if len(nonce) != 12:
            raise ValueError("invalid_gcm_nonce")
        try:
            plaintext = AESGCM(_key(recipient_key)).decrypt(nonce,ciphertext,_canonical(_headers(workspace,recipient,key_id)))
        except InvalidTag as exc:
            raise ValueError("transport_authentication_failed") from exc
        try:
            envelope = json.loads(plaintext.decode("utf-8"))
        except (UnicodeDecodeError,json.JSONDecodeError) as exc:
            raise ValueError("invalid_decrypted_envelope") from exc
        if not isinstance(envelope,dict) or envelope.get("workspace_id") != workspace or envelope.get("recipient_entity_id") != recipient:
            raise ValueError("decrypted_envelope_scope_mismatch")
        return envelope

class ReliableDeliveryOutbox:
    """Local outbox. send, verify_ack and authorize_delivery are trusted host adapters."""
    def __init__(self, *, send: Callable[[dict[str,Any]],dict[str,Any]],
        verify_ack: Callable[[dict[str,Any],str],bool], authorize_delivery: Callable[[str],bool],
        db_path: str = ".xparallel/transport_outbox.sqlite3", max_attempts: int = 5,
        max_pending: int = 1000, rate_limit: int = 60, rate_window_seconds: int = 60):
        if not all(callable(x) for x in (send,verify_ack,authorize_delivery)):
            raise TypeError("trusted_delivery_adapters_required")
        for value, low, high, name in ((max_attempts,1,20,"max_attempts"),(max_pending,1,10000,"max_pending"),
            (rate_limit,1,10000,"rate_limit"),(rate_window_seconds,1,3600,"rate_window_seconds")):
            if not isinstance(value,int) or isinstance(value,bool) or not low <= value <= high:
                raise ValueError(f"invalid_{name}")
        self._send,self._verify_ack,self._authorize = send,verify_ack,authorize_delivery
        self._max_attempts,self._max_pending,self._rate_limit,self._rate_window = max_attempts,max_pending,rate_limit,rate_window_seconds
        if db_path != ":memory:": Path(db_path).expanduser().resolve().parent.mkdir(parents=True,exist_ok=True)
        self._db=sqlite3.connect(db_path,timeout=10,check_same_thread=False); self._db.row_factory=sqlite3.Row
        self._db.execute("""CREATE TABLE IF NOT EXISTS transport_outbox (
            workspace_id TEXT NOT NULL,message_id TEXT NOT NULL,sender_entity_id TEXT NOT NULL,
            packet_json TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,
            next_attempt_at REAL NOT NULL,last_error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
            PRIMARY KEY(workspace_id,message_id))""")
        self._db.execute("""CREATE TABLE IF NOT EXISTS transport_attempts (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,workspace_id TEXT NOT NULL,
            sender_entity_id TEXT NOT NULL,attempted_at REAL NOT NULL)""")
        self._db.commit()

    def enqueue(self, *, workspace_id: str, message_id: str, sender_entity_id: str,
        encrypted_packet: dict[str,Any]) -> dict[str,Any]:
        workspace,message,sender=(_id(workspace_id,"workspace_id"),_id(message_id,"message_id"),_id(sender_entity_id,"sender_entity_id"))
        if not isinstance(encrypted_packet,dict): raise ValueError("encrypted_packet_required")
        encoded=_canonical(encrypted_packet).decode("utf-8"); now=datetime.now(timezone.utc).isoformat()
        with _LOCK,self._db:
            existing=self._db.execute("SELECT status FROM transport_outbox WHERE workspace_id=? AND message_id=?",(workspace,message)).fetchone()
            if existing: return {"queued":False,"duplicate":True,"status":existing["status"]}
            pending=self._db.execute("SELECT COUNT(*) FROM transport_outbox WHERE status IN ('pending','retrying')").fetchone()[0]
            if pending >= self._max_pending: raise ValueError("outbox_quota_exceeded")
            self._db.execute("INSERT INTO transport_outbox VALUES (?,?,?,?,'pending',0,?,NULL,?,?,?)",
                (workspace,message,sender,encoded,0,now,now))
        return {"queued":True,"duplicate":False,"status":"pending"}

    def dispatch_one(self,workspace_id: str,message_id: str)->dict[str,Any]:
        workspace,message=_id(workspace_id,"workspace_id"),_id(message_id,"message_id")
        now_epoch=datetime.now(timezone.utc).timestamp()
        with _LOCK:
            row=self._db.execute("SELECT * FROM transport_outbox WHERE workspace_id=? AND message_id=?",(workspace,message)).fetchone()
            if row is None: raise LookupError("outbox_message_not_found")
            if row["status"] in {"delivered","dead_letter","revoked"}: return {"status":row["status"],"attempts":row["attempts"]}
            if row["next_attempt_at"] > now_epoch: return {"status":row["status"],"attempts":row["attempts"],"deferred":True}
            recent=self._db.execute("SELECT COUNT(*) FROM transport_attempts WHERE workspace_id=? AND sender_entity_id=? AND attempted_at>?",
                (workspace,row["sender_entity_id"],now_epoch-self._rate_window)).fetchone()[0]
            if recent >= self._rate_limit: return {"status":row["status"],"attempts":row["attempts"],"rate_limited":True}
        if not self._authorize(message):
            with _LOCK,self._db:
                self._db.execute("UPDATE transport_outbox SET status='revoked',last_error='authorization_revoked',updated_at=? WHERE workspace_id=? AND message_id=?",
                    (datetime.now(timezone.utc).isoformat(),workspace,message))
            return {"status":"revoked","attempts":row["attempts"]}
        attempted=datetime.now(timezone.utc)
        with _LOCK,self._db:
            self._db.execute("INSERT INTO transport_attempts(workspace_id,sender_entity_id,attempted_at) VALUES (?,?,?)",
                (workspace,row["sender_entity_id"],attempted.timestamp()))
            self._db.execute("UPDATE transport_outbox SET attempts=attempts+1,updated_at=? WHERE workspace_id=? AND message_id=?",
                (attempted.isoformat(),workspace,message))
        try:
            ack=self._send(json.loads(row["packet_json"]))
            if not isinstance(ack,dict) or not self._verify_ack(ack,message): raise ValueError("recipient_acknowledgement_invalid")
            with _LOCK,self._db:
                self._db.execute("UPDATE transport_outbox SET status='delivered',last_error=NULL,updated_at=? WHERE workspace_id=? AND message_id=?",
                    (datetime.now(timezone.utc).isoformat(),workspace,message))
            return {"status":"delivered","attempts":row["attempts"]+1}
        except Exception as exc:
            attempts=row["attempts"]+1; dead=attempts>=self._max_attempts
            delay=min(300,2**attempts); status="dead_letter" if dead else "retrying"; now=datetime.now(timezone.utc)
            with _LOCK,self._db:
                self._db.execute("UPDATE transport_outbox SET status=?,last_error=?,next_attempt_at=?,updated_at=? WHERE workspace_id=? AND message_id=?",
                    (status,type(exc).__name__[:80],now.timestamp()+delay,now.isoformat(),workspace,message))
            return {"status":status,"attempts":attempts,"retry_after_seconds":None if dead else delay}

    def status(self,workspace_id: str,message_id: str)->dict[str,Any]|None:
        row=self._db.execute("SELECT status,attempts,last_error,next_attempt_at,created_at,updated_at FROM transport_outbox WHERE workspace_id=? AND message_id=?",
            (_id(workspace_id,"workspace_id"),_id(message_id,"message_id"))).fetchone()
        return dict(row) if row else None

    def close(self)->None:
        with _LOCK:self._db.close()
