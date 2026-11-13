"""Owner-controlled, signed local XParallel federation discovery registry.

This module is a local discovery prototype, not a public network registry.
Authentication, owner authorization and federation trust policy are injected.
"""
from __future__ import annotations
import base64, json, re, secrets, sqlite3, threading, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from xparallel.identity_trust import EntityKeyStore

_LOCK=threading.RLock()
_DOMAIN=b"XPARALLEL-FEDERATION-RECORD-V1\n"
_SEMVER=re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

def _canonical(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")

def _id(value:Any,field:str)->str:
    if not isinstance(value,str) or not value.strip() or len(value)>200:
        raise ValueError(f"invalid_{field}")
    return value

def _principal(value:Any)->dict[str,str]:
    if not isinstance(value,dict) or value.get("authenticated") is not True:
        raise PermissionError("caller_not_authenticated")
    return {"workspace_id":_id(value.get("workspace_id"),"workspace_id"),
            "subject":_id(value.get("subject"),"subject")}

def _version(value:Any)->tuple[int,int,int]:
    if not isinstance(value,str) or not _SEMVER.fullmatch(value):
        raise ValueError("invalid_protocol_version")
    return tuple(int(part) for part in value.split("."))

def _record_bytes(record:dict[str,Any])->bytes:
    return _DOMAIN+_canonical(record)

class FederationRegistry:
    """Signed registry records with owner visibility, trust checks and anti-enumeration."""
    def __init__(self,*,key_store:EntityKeyStore,authenticate:Callable[[Any],dict[str,Any]],
        authorize_publish:Callable[[dict[str,str],str],bool],
        resolve_entity:Callable[[str,str],dict[str,Any]|None],
        trust_peer:Callable[[dict[str,str],str],bool],
        db_path:str=".xparallel/federation.sqlite3",rate_limit:int=30,rate_window_seconds:int=60):
        if not isinstance(key_store,EntityKeyStore): raise TypeError("trusted_entity_key_store_required")
        if not all(callable(x) for x in (authenticate,authorize_publish,resolve_entity,trust_peer)):
            raise TypeError("federation_trust_adapters_required")
        if not isinstance(rate_limit,int) or isinstance(rate_limit,bool) or not 1<=rate_limit<=1000:
            raise ValueError("invalid_rate_limit")
        if not isinstance(rate_window_seconds,int) or isinstance(rate_window_seconds,bool) or not 1<=rate_window_seconds<=3600:
            raise ValueError("invalid_rate_window")
        self._keys,self._authenticate,self._authorize=key_store,authenticate,authorize_publish
        self._resolve,self._trust=resolve_entity,trust_peer
        self._rate_limit,self._rate_window=rate_limit,rate_window_seconds
        if db_path!=":memory:": Path(db_path).expanduser().resolve().parent.mkdir(parents=True,exist_ok=True)
        self._db=sqlite3.connect(db_path,timeout=10,check_same_thread=False); self._db.row_factory=sqlite3.Row
        self._db.execute("""CREATE TABLE IF NOT EXISTS federation_records(
            record_id TEXT PRIMARY KEY,issuer_workspace TEXT NOT NULL,entity_id TEXT NOT NULL,key_id TEXT NOT NULL,
            record_json TEXT NOT NULL,signature_b64 TEXT NOT NULL,issued_at TEXT NOT NULL,expires_at TEXT NOT NULL,
            revoked_at TEXT)""")
        self._db.execute("""CREATE INDEX IF NOT EXISTS federation_visibility
            ON federation_records(issuer_workspace,entity_id,expires_at,revoked_at)""")
        self._db.execute("""CREATE TABLE IF NOT EXISTS federation_queries(
            workspace_id TEXT NOT NULL,subject TEXT NOT NULL,queried_at REAL NOT NULL)""")
        self._db.commit()

    def _identity(self,session:Any)->dict[str,str]:
        return _principal(self._authenticate(session))

    def publish(self,session:Any,*,entity_id:str,key_id:str,visibility:str,
        private_key:Any,ttl_seconds:int=86400,allowed_peers:list[str]|None=None)->dict[str,Any]:
        identity=self._identity(session)
        entity,key=_id(entity_id,"entity_id"),_id(key_id,"key_id")
        if visibility not in {"public","allowlist","private"}: raise ValueError("invalid_visibility")
        peers=allowed_peers or []
        if not isinstance(peers,list) or len(peers)>100 or any(not isinstance(x,str) or not x.strip() or len(x)>200 for x in peers):
            raise ValueError("invalid_allowed_peers")
        peers=sorted(set(peers))
        if visibility=="allowlist" and not peers: raise ValueError("allowlist_requires_peers")
        if visibility!="allowlist" and peers: raise ValueError("peers_only_valid_for_allowlist")
        if not isinstance(ttl_seconds,int) or isinstance(ttl_seconds,bool) or not 60<=ttl_seconds<=604800:
            raise ValueError("record_ttl_out_of_range")
        if not self._authorize(identity,entity): raise PermissionError("entity_publish_not_authorized")
        key_record=self._keys.get_key(identity["workspace_id"],entity,key)
        if not key_record or key_record.get("status")!="active": raise PermissionError("active_entity_key_required")
        if not hasattr(private_key,"sign"): raise ValueError("ed25519_private_key_required")
        source=self._resolve(identity["workspace_id"],entity)
        if not isinstance(source,dict) or not isinstance(source.get("manifest"),dict):
            raise LookupError("authoritative_entity_record_missing")
        manifest=source["manifest"]
        if manifest.get("entity_id")!=entity or manifest.get("owner",{}).get("subject")!=identity["subject"]:
            raise PermissionError("entity_owner_mismatch")
        if manifest.get("status") in {"suspended","revoked","retired"}:
            raise PermissionError("entity_not_discoverable")
        protocols=manifest.get("protocols")
        if not isinstance(protocols,list): raise ValueError("authoritative_protocols_missing")
        safe_protocols=[]
        for item in protocols:
            if not isinstance(item,dict) or not isinstance(item.get("id"),str): continue
            _version(item.get("version"))
            safe_protocols.append({"id":item["id"],"version":item["version"]})
        declared=[]
        for item in manifest.get("capabilities",[]):
            if isinstance(item,dict) and item.get("status") in {"declared","under_review"} and isinstance(item.get("capability_id"),str):
                declared.append({"capability_id":item["capability_id"],"version":str(item.get("version","")),"status":"declared"})
        now=datetime.now(timezone.utc); expires=now+timedelta(seconds=ttl_seconds)
        record={"record_id":uuid.uuid4().hex,"issuer_workspace":identity["workspace_id"],
            "owner_subject":identity["subject"],"entity_id":entity,"key_id":key,
            "manifest_revision":int(source.get("revision",0)),"entity_type":manifest.get("entity_type"),
            "display_name":manifest.get("display_name"),"protocols":safe_protocols,
            "declared_capabilities":declared,"visibility":visibility,"allowed_peers":peers,
            "issued_at":now.isoformat(),"expires_at":expires.isoformat()}
        signature=base64.b64encode(private_key.sign(_record_bytes(record))).decode("ascii")
        try:
            public=base64.b64decode(key_record["public_key_b64"],validate=True)
            Ed25519PublicKey.from_public_bytes(public).verify(base64.b64decode(signature),_record_bytes(record))
        except (InvalidSignature,ValueError,TypeError,KeyError) as exc:
            raise PermissionError("signing_key_does_not_match_active_registry_key") from exc
        with _LOCK,self._db:
            self._db.execute("INSERT INTO federation_records VALUES (?,?,?,?,?,?,?,?,NULL)",
                (record["record_id"],identity["workspace_id"],entity,key,_canonical(record).decode(),signature,
                 record["issued_at"],record["expires_at"]))
        return {"published":True,"record_id":record["record_id"],"visibility":visibility,
                "expires_at":record["expires_at"],"capabilities_published":"declared_only"}

    def discover(self,session:Any,*,protocol_id:str,minimum_version:str,
        capability_id:str|None=None,limit:int=20)->dict[str,Any]:
        identity=self._identity(session)
        protocol=_id(protocol_id,"protocol_id"); required=_version(minimum_version)
        capability=_id(capability_id,"capability_id") if capability_id is not None else None
        if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=50:
            raise ValueError("invalid_discovery_limit")
        now=datetime.now(timezone.utc); epoch=now.timestamp()
        with _LOCK,self._db:
            count=self._db.execute("SELECT COUNT(*) FROM federation_queries WHERE workspace_id=? AND subject=? AND queried_at>?",
                (identity["workspace_id"],identity["subject"],epoch-self._rate_window)).fetchone()[0]
            if count>=self._rate_limit: raise PermissionError("discovery_rate_limited")
            self._db.execute("INSERT INTO federation_queries VALUES (?,?,?)",(identity["workspace_id"],identity["subject"],epoch))
            rows=self._db.execute("SELECT * FROM federation_records WHERE expires_at>? AND revoked_at IS NULL ORDER BY issued_at DESC LIMIT 500",
                (now.isoformat(),)).fetchall()
        results=[]
        for row in rows:
            try:
                record=json.loads(row["record_json"])
                if record["visibility"]=="private": continue
                if record["visibility"]=="allowlist" and identity["subject"] not in record["allowed_peers"]: continue
                if not self._trust(identity,row["issuer_workspace"]): continue
                key=self._keys.get_key(row["issuer_workspace"],row["entity_id"],row["key_id"])
                if not key or key.get("status")!="active": continue
                public=base64.b64decode(key["public_key_b64"],validate=True)
                Ed25519PublicKey.from_public_bytes(public).verify(base64.b64decode(row["signature_b64"]),_record_bytes(record))
                compatible=False
                for item in record["protocols"]:
                    if item.get("id")==protocol:
                        remote=_version(item.get("version"))
                        compatible=remote[0]==required[0] and remote>=required
                        if compatible: break
                if not compatible: continue
                if capability and not any(c.get("capability_id")==capability for c in record["declared_capabilities"]): continue
                results.append({"record_id":record["record_id"],"issuer_workspace":record["issuer_workspace"],
                    "entity_id":record["entity_id"],"entity_type":record["entity_type"],
                    "display_name":record["display_name"],"protocols":record["protocols"],
                    "declared_capabilities":record["declared_capabilities"],"record_expires_at":record["expires_at"],
                    "capability_evidence":"not_included; declaration is not verification"})
                if len(results)>=limit: break
            except (KeyError,ValueError,TypeError,InvalidSignature):
                continue
        return {"results":results,"count":len(results),"limit":limit}

    def revoke(self,session:Any,record_id:str)->dict[str,Any]:
        identity=self._identity(session); record_id=_id(record_id,"record_id")
        with _LOCK,self._db:
            row=self._db.execute("SELECT entity_id,issuer_workspace FROM federation_records WHERE record_id=?",(record_id,)).fetchone()
            if row is None or row["issuer_workspace"]!=identity["workspace_id"]: raise LookupError("federation_record_not_found")
            if not self._authorize(identity,row["entity_id"]): raise PermissionError("entity_publish_not_authorized")
            now=datetime.now(timezone.utc).isoformat()
            self._db.execute("UPDATE federation_records SET revoked_at=? WHERE record_id=? AND revoked_at IS NULL",(now,record_id))
        return {"revoked":True,"record_id":record_id}

    def close(self)->None:
        with _LOCK:self._db.close()
