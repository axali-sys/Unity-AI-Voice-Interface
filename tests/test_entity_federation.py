import base64, tempfile, unittest
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from xparallel.identity_trust import EntityKeyStore, owner_challenge_message
from xparallel.entity_federation import FederationRegistry

class FederationRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); root=Path(self.temp.name)
        self.owner={"authenticated":True,"workspace_id":"ws-a","subject":"owner-a"}
        self.peer={"authenticated":True,"workspace_id":"ws-b","subject":"peer-b"}
        self.private=Ed25519PrivateKey.generate()
        raw=self.private.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        self.keys=EntityKeyStore(str(root/"keys.sqlite3"))
        self.keys.register_pending_key("ws-a","entity-123456","key-a",base64.b64encode(raw).decode())
        challenge=self.keys.create_owner_challenge("ws-a","entity-123456","key-a")
        self.keys.verify_owner_challenge("ws-a","entity-123456","key-a",challenge["challenge_id"],
          base64.b64encode(self.private.sign(base64.b64decode(challenge["message_b64"]))).decode())
        self.manifest={"entity_id":"entity-123456","entity_type":"agent","display_name":"Research Entity",
          "status":"active","owner":{"subject":"owner-a"},"protocols":[{"id":"xparallel","version":"1.2.0"}],
          "capabilities":[{"capability_id":"research.read","version":"1.0.0","status":"declared"}]}
        self.registry=FederationRegistry(key_store=self.keys,
          authenticate=lambda session: self.owner if session=="owner" else self.peer if session=="peer" else {"authenticated":False},
          authorize_publish=lambda principal,eid: principal["subject"]=="owner-a" and eid=="entity-123456",
          resolve_entity=lambda ws,eid: {"manifest":self.manifest,"revision":1} if (ws,eid)==("ws-a","entity-123456") else None,
          trust_peer=lambda principal,issuer: issuer=="ws-a",db_path=str(root/"federation.sqlite3"))
    def tearDown(self):
        self.registry.close(); self.keys.close(); self.temp.cleanup()
    def publish(self,visibility="public",peers=None):
        return self.registry.publish("owner",entity_id="entity-123456",key_id="key-a",
          visibility=visibility,allowed_peers=peers,private_key=self.private)
    def test_signed_public_record_discovery_and_protocol_compatibility(self):
        self.publish()
        found=self.registry.discover("peer",protocol_id="xparallel",minimum_version="1.0.0",capability_id="research.read")
        self.assertEqual(found["count"],1)
        self.assertEqual(found["results"][0]["declared_capabilities"][0]["status"],"declared")
        self.assertIn("not verification",found["results"][0]["capability_evidence"])
        self.assertEqual(self.registry.discover("peer",protocol_id="xparallel",minimum_version="2.0.0")["count"],0)
    def test_visibility_owner_control_and_revocation(self):
        record=self.publish("allowlist",["peer-b"])
        self.assertEqual(self.registry.discover("peer",protocol_id="xparallel",minimum_version="1.0.0")["count"],1)
        denied={"authenticated":True,"workspace_id":"ws-c","subject":"other"}
        self.assertEqual(self.registry.discover("owner",protocol_id="xparallel",minimum_version="1.0.0")["count"],0)
        self.registry.revoke("owner",record["record_id"])
        self.assertEqual(self.registry.discover("peer",protocol_id="xparallel",minimum_version="1.0.0")["count"],0)
    def test_private_record_never_appears_and_wrong_key_is_rejected(self):
        self.publish("private")
        self.assertEqual(self.registry.discover("peer",protocol_id="xparallel",minimum_version="1.0.0")["count"],0)
        other=Ed25519PrivateKey.generate()
        with self.assertRaises(PermissionError):
            self.registry.publish("owner",entity_id="entity-123456",key_id="key-a",
              visibility="public",private_key=other)
    def test_authentication_owner_binding_and_allowlist_required(self):
        with self.assertRaises(PermissionError):
            self.registry.publish("bad",entity_id="entity-123456",key_id="key-a",visibility="public",private_key=self.private)
        with self.assertRaises(ValueError):
            self.registry.publish("owner",entity_id="entity-123456",key_id="key-a",visibility="allowlist",private_key=self.private)
        self.manifest["owner"]["subject"]="someone-else"
        with self.assertRaises(PermissionError):
            self.publish()
    def test_query_rate_limit(self):
        self.registry.close()
        self.registry=FederationRegistry(key_store=self.keys,
          authenticate=lambda session:self.peer,authorize_publish=lambda p,e:True,
          resolve_entity=lambda w,e:None,trust_peer=lambda p,w:True,
          db_path=str(Path(self.temp.name)/"rate.sqlite3"),rate_limit=1)
        self.registry.discover("peer",protocol_id="xparallel",minimum_version="1.0.0")
        with self.assertRaises(PermissionError):
            self.registry.discover("peer",protocol_id="xparallel",minimum_version="1.0.0")
if __name__=="__main__": unittest.main()
