"""Permission-scoped, encrypted entity memory with provenance and retention."""
from __future__ import annotations
import base64, hashlib, json, re, secrets, sqlite3, threading, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_LOCK=threading.RLock()
_SHA=re.compile(r"^[a-f0-9]{64}$")
_MAX_CONTENT=1_000_000

def _canonical(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")

def _id(value:Any,field:str)->str:
    if not isinstance(value,str) or not value.strip() or len(value)>200: raise ValueError(f"invalid_{field}")
    return value

def _key(value:Any)->bytes:
    if not isinstance(value,bytes) or len(value)!=32: raise ValueError("memory_key_must_be_256_bit_bytes")
    return value

def retrieval_metrics(expected_ids:list[str],retrieved_ids:list[str])->dict[str,float]:
    """Small deterministic retrieval evaluator; expected IDs are the relevant set."""
    expected=set(expected_ids); retrieved=list(retrieved_ids)
    hits=sum(1 for item in retrieved if item in expected)
    precision=hits/len(retrieved) if retrieved else 0.0
    recall=hits/len(expected) if expected else 0.0
    reciprocal=next((1.0/(i+1) for i,item in enumerate(retrieved) if item in expected),0.0)
    return {"precision":precision,"recall":recall,"reciprocal_rank":reciprocal}

class EntityMemoryStore:
    """Encrypted SQLite store. Authentication, ACL and key resolution are host trust roots."""
    def __init__(self,*,authenticate:Callable[[Any],dict[str,Any]],
        authorize:Callable[[dict[str,str],str,str],bool],
        resolve_encryption_key:Callable[[str,str],bytes],
        db_path:str=".xparallel/entity_memory.sqlite3"):
        if not all(callable(x) for x in (authenticate,authorize,resolve_encryption_key)):
            raise TypeError("trusted_memory_adapters_required")
        self._authenticate,self._authorize,self._resolve_key=authenticate,authorize,resolve_encryption_key
        if db_path!=":memory:": Path(db_path).expanduser().resolve().parent.mkdir(parents=True,exist_ok=True)
        self._db=sqlite3.connect(db_path,timeout=10,check_same_thread=False); self._db.row_factory=sqlite3.Row
        self._db.execute("""CREATE TABLE IF NOT EXISTS entity_memories(
            workspace_id TEXT NOT NULL,entity_id TEXT NOT NULL,memory_id TEXT NOT NULL,
            content_digest TEXT NOT NULL,nonce_b64 TEXT NOT NULL,ciphertext_b64 TEXT NOT NULL,
            created_at TEXT NOT NULL,expires_at TEXT NOT NULL,PRIMARY KEY(workspace_id,entity_id,memory_id),
            UNIQUE(workspace_id,entity_id,content_digest))""")
        self._db.execute("CREATE INDEX IF NOT EXISTS entity_memory_scope ON entity_memories(workspace_id,entity_id,expires_at)")
        self._db.commit()

    def _principal(self,session:Any)->dict[str,str]:
        raw=self._authenticate(session)
        if not isinstance(raw,dict) or raw.get("authenticated") is not True: raise PermissionError("caller_not_authenticated")
        return {"workspace_id":_id(raw.get("workspace_id"),"workspace_id"),"subject":_id(raw.get("subject"),"subject")}

    def _allowed(self,principal:dict[str,str],entity_id:str,action:str)->None:
        if self._authorize(principal,entity_id,action) is not True: raise PermissionError("memory_access_denied")

    def _encrypt(self,workspace:str,entity:str,memory_id:str,payload:dict[str,Any])->tuple[str,str]:
        key=_key(self._resolve_key(workspace,entity)); nonce=secrets.token_bytes(12)
        aad=_canonical({"workspace_id":workspace,"entity_id":entity,"memory_id":memory_id,"version":"1"})
        encrypted=AESGCM(key).encrypt(nonce,_canonical(payload),aad)
        return base64.b64encode(nonce).decode(),base64.b64encode(encrypted).decode()

    def _decrypt(self,row:sqlite3.Row)->dict[str,Any]:
        workspace,entity,memory=row["workspace_id"],row["entity_id"],row["memory_id"]
        try:
            nonce=base64.b64decode(row["nonce_b64"],validate=True); ciphertext=base64.b64decode(row["ciphertext_b64"],validate=True)
            aad=_canonical({"workspace_id":workspace,"entity_id":entity,"memory_id":memory,"version":"1"})
            plain=AESGCM(_key(self._resolve_key(workspace,entity))).decrypt(nonce,ciphertext,aad)
            value=json.loads(plain.decode("utf-8"))
        except (ValueError,TypeError,InvalidTag,UnicodeDecodeError,json.JSONDecodeError) as exc:
            raise ValueError("memory_decryption_or_integrity_failed") from exc
        if not isinstance(value,dict): raise ValueError("invalid_memory_payload")
        return value

    def save(self,session:Any,*,entity_id:str,content:str,source_type:str,source_ref:str,
        source_digest:str,retention_seconds:int=2592000,tags:list[str]|None=None)->dict[str,Any]:
        principal=self._principal(session); entity=_id(entity_id,"entity_id")
        self._allowed(principal,entity,"write")
        if not isinstance(content,str) or not content.strip() or len(content.encode("utf-8"))>_MAX_CONTENT:
            raise ValueError("invalid_memory_content")
        source_type=_id(source_type,"source_type"); source_ref=_id(source_ref,"source_ref")
        if not isinstance(source_digest,str) or not _SHA.fullmatch(source_digest): raise ValueError("source_digest_must_be_sha256")
        if not isinstance(retention_seconds,int) or isinstance(retention_seconds,bool) or not 60<=retention_seconds<=31536000:
            raise ValueError("retention_out_of_range")
        if not isinstance(tags,list) or len(tags)>30 or any(not isinstance(t,str) or len(t)>80 for t in tags):
            raise ValueError("invalid_memory_tags")
        content_digest=hashlib.sha256(content.encode()).hexdigest()
        now=datetime.now(timezone.utc); expires=now+timedelta(seconds=retention_seconds)
        memory_id=uuid.uuid4().hex
        payload={"content":content,"provenance":{"source_type":source_type,"source_ref":source_ref,
            "source_digest":source_digest,"content_digest":content_digest,"created_by":principal["subject"],
            "created_at":now.isoformat()},"tags":tags}
        nonce,ciphertext=self._encrypt(principal["workspace_id"],entity,memory_id,payload)
        with _LOCK,self._db:
            existing=self._db.execute("SELECT memory_id FROM entity_memories WHERE workspace_id=? AND entity_id=? AND content_digest=?",
                (principal["workspace_id"],entity,content_digest)).fetchone()
            if existing: return {"memory_id":existing["memory_id"],"created":False,"content_digest":content_digest}
            self._db.execute("INSERT INTO entity_memories VALUES (?,?,?,?,?,?,?,?)",
                (principal["workspace_id"],entity,memory_id,content_digest,nonce,ciphertext,now.isoformat(),expires.isoformat()))
        return {"memory_id":memory_id,"created":True,"content_digest":content_digest,"expires_at":expires.isoformat()}

    def search(self,session:Any,*,entity_id:str,query:str,limit:int=10)->list[dict[str,Any]]:
        principal=self._principal(session); entity=_id(entity_id,"entity_id"); self._allowed(principal,entity,"read")
        terms=[x.casefold() for x in str(query).split() if len(x)>1]
        if not terms: return []
        if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=50: raise ValueError("invalid_memory_limit")
        now=datetime.now(timezone.utc).isoformat()
        with _LOCK,self._db:
            self._db.execute("DELETE FROM entity_memories WHERE workspace_id=? AND entity_id=? AND expires_at<=?",
                (principal["workspace_id"],entity,now))
            rows=self._db.execute("SELECT * FROM entity_memories WHERE workspace_id=? AND entity_id=? AND expires_at>? ORDER BY created_at DESC LIMIT 500",
                (principal["workspace_id"],entity,now)).fetchall()
        results=[]
        for row in rows:
            payload=self._decrypt(row); text=(payload["content"]+" "+" ".join(payload["tags"])).casefold()
            score=sum(text.count(term) for term in terms)
            if score: results.append({"memory_id":row["memory_id"],"content":payload["content"],
                "provenance":payload["provenance"],"tags":payload["tags"],"score":score,"expires_at":row["expires_at"]})
        results.sort(key=lambda item:(item["score"],item["provenance"]["created_at"]),reverse=True)
        return results[:limit]

    def export(self,session:Any,*,entity_id:str)->dict[str,Any]:
        principal=self._principal(session); entity=_id(entity_id,"entity_id"); self._allowed(principal,entity,"export")
        now=datetime.now(timezone.utc).isoformat()
        rows=self._db.execute("SELECT * FROM entity_memories WHERE workspace_id=? AND entity_id=? AND expires_at>? ORDER BY created_at",
            (principal["workspace_id"],entity,now)).fetchall()
        return {"workspace_id":principal["workspace_id"],"entity_id":entity,
            "memories":[{"memory_id":row["memory_id"],**self._decrypt(row),"expires_at":row["expires_at"]} for row in rows]}

    def delete(self,session:Any,*,entity_id:str,memory_id:str)->bool:
        principal=self._principal(session); entity=_id(entity_id,"entity_id"); memory=_id(memory_id,"memory_id")
        self._allowed(principal,entity,"delete")
        with _LOCK,self._db:
            cursor=self._db.execute("DELETE FROM entity_memories WHERE workspace_id=? AND entity_id=? AND memory_id=?",
                (principal["workspace_id"],entity,memory))
        return cursor.rowcount==1

    def close(self)->None:
        with _LOCK:self._db.close()
