import base64, tempfile, unittest
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from xparallel.identity_trust import EntityKeyStore
from xparallel.entity_messaging import EntityMessageService
from xparallel.sdk import XParallelEntitySDK
from xparallel.protocol_compat import is_backward_compatible,negotiate_protocol

class DeveloperConformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); root=Path(self.temp.name)
        self.keys=EntityKeyStore(str(root/"keys.sqlite3")); self.private_a=Ed25519PrivateKey.generate(); self.private_b=Ed25519PrivateKey.generate()
        self._activate("entity-alpha","key-a",self.private_a); self._activate("entity-bravo","key-b",self.private_b)
        self.messages=EntityMessageService(self.keys,str(root/"messages.sqlite3"))
        self.key_a=b"a"*32; self.key_b=b"b"*32
        self.sdk_a=XParallelEntitySDK(workspace_id="ws-demo",entity_id="entity-alpha",key_id="key-a",private_key=self.private_a,
          message_service=self.messages,resolve_recipient_key=lambda ws,e:{"key_id":"enc-b","key":self.key_b})
        self.sdk_b=XParallelEntitySDK(workspace_id="ws-demo",entity_id="entity-bravo",key_id="key-b",private_key=self.private_b,
          message_service=self.messages,resolve_recipient_key=lambda ws,e:{"key_id":"enc-a","key":self.key_a})
    def _activate(self,entity,key_id,private):
        raw=private.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        self.keys.register_pending_key("ws-demo",entity,key_id,base64.b64encode(raw).decode())
        challenge=self.keys.create_owner_challenge("ws-demo",entity,key_id)
        self.keys.verify_owner_challenge("ws-demo",entity,key_id,challenge["challenge_id"],
          base64.b64encode(private.sign(base64.b64decode(challenge["message_b64"]))).decode())
    def tearDown(self):
        self.messages.close(); self.keys.close(); self.temp.cleanup()
    def test_independent_entities_exchange_encrypted_signed_message(self):
        packet=self.sdk_a.create_packet(recipient_entity_id="entity-bravo",message_type="task.request",
          body={"task":"summarize","scope":"public-documents"})
        received=self.sdk_b.receive_packet(packet,recipient_key_id="enc-b",recipient_key=self.key_b)
        self.assertEqual(received["body"]["task"],"summarize")
        with self.assertRaises(ValueError):
            self.sdk_b.receive_packet(packet,recipient_key_id="enc-b",recipient_key=self.key_b)
    def test_wrong_recipient_and_wrong_encryption_key_are_rejected(self):
        packet=self.sdk_a.create_packet(recipient_entity_id="entity-bravo",message_type="task.request",body={"x":1})
        with self.assertRaises(ValueError):
            self.sdk_b.receive_packet(packet,recipient_key_id="enc-b",recipient_key=b"x"*32)
    def test_protocol_compatibility_is_deterministic(self):
        self.assertTrue(is_backward_compatible("1.4.0","1.2.0"))
        self.assertFalse(is_backward_compatible("2.0.0","1.2.0"))
        self.assertEqual(negotiate_protocol(["1.0.0","1.2.0","2.0.0"],["1.2.0","2.1.0"]),"1.2.0")
        self.assertIsNone(negotiate_protocol(["1.0.0"],["2.0.0"]))
if __name__=="__main__": unittest.main()
