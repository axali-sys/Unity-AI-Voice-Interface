import hashlib, tempfile, unittest
from pathlib import Path
from xparallel.entity_memory import EntityMemoryStore, retrieval_metrics

class EntityMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.key=b"m"*32
        self.principal={"authenticated":True,"workspace_id":"ws-a","subject":"owner-a"}
        self.allowed=True
        self.store=EntityMemoryStore(authenticate=lambda s:self.principal if s=="valid" else {"authenticated":False},
          authorize=lambda p,e,a:self.allowed and p["workspace_id"]=="ws-a" and e=="entity-123456" and a in {"read","write","export","delete"},
          resolve_encryption_key=lambda w,e:self.key if (w,e)==("ws-a","entity-123456") else b"x"*32,
          db_path=str(Path(self.temp.name)/"memory.sqlite3"))
    def tearDown(self): self.store.close(); self.temp.cleanup()
    def save(self,content="Evidence from source A"):
        return self.store.save("valid",entity_id="entity-123456",content=content,source_type="document",
          source_ref="source:doc-1",source_digest=hashlib.sha256(b"source").hexdigest(),tags=["research"])
    def test_encrypted_storage_provenance_search_and_export(self):
        result=self.save()
        raw=self.store._db.execute("SELECT ciphertext_b64 FROM entity_memories").fetchone()[0]
        self.assertNotIn("Evidence from source A",raw)
        found=self.store.search("valid",entity_id="entity-123456",query="Evidence research")
        self.assertEqual(found[0]["memory_id"],result["memory_id"])
        self.assertEqual(found[0]["provenance"]["source_ref"],"source:doc-1")
        self.assertEqual(len(self.store.export("valid",entity_id="entity-123456")["memories"]),1)
    def test_workspace_entity_and_permission_isolation(self):
        self.save()
        with self.assertRaises(PermissionError):
            self.store.search("invalid",entity_id="entity-123456",query="Evidence")
        self.allowed=False
        with self.assertRaises(PermissionError):
            self.store.export("valid",entity_id="entity-123456")
    def test_integrity_failure_is_detected(self):
        self.save()
        self.store._db.execute("UPDATE entity_memories SET ciphertext_b64='AAAA'"); self.store._db.commit()
        with self.assertRaises(ValueError):
            self.store.search("valid",entity_id="entity-123456",query="Evidence")
    def test_delete_and_retention_validation(self):
        item=self.save()
        self.assertTrue(self.store.delete("valid",entity_id="entity-123456",memory_id=item["memory_id"]))
        with self.assertRaises(ValueError):
            self.store.save("valid",entity_id="entity-123456",content="x",source_type="doc",source_ref="r",
              source_digest=hashlib.sha256(b"x").hexdigest(),retention_seconds=0)
    def test_retrieval_metrics(self):
        metrics=retrieval_metrics(["a","b"],["b","x","a"])
        self.assertAlmostEqual(metrics["precision"],2/3)
        self.assertEqual(metrics["recall"],1.0)
        self.assertAlmostEqual(metrics["reciprocal_rank"],1/1)
if __name__=="__main__": unittest.main()
