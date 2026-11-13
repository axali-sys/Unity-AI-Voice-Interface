import json, tempfile, unittest
from xparallel.secure_transport import EncryptedEnvelopeCodec, ReliableDeliveryOutbox

class EncryptedTransportTests(unittest.TestCase):
    def setUp(self):
        self.key=b"k"*32
        self.envelope={"schema_version":"1.0","message_id":"msg-1","workspace_id":"ws-a",
          "sender_entity_id":"sender","sender_key_id":"key-s","recipient_entity_id":"recipient",
          "message_type":"hello","issued_at":"2026-01-01T00:00:00+00:00",
          "expires_at":"2026-01-01T00:05:00+00:00","body":{"hello":"world"},
          "body_sha256":"0"*64,"signature":"test-signature"}
    def test_encrypted_packet_round_trip(self):
        packet=EncryptedEnvelopeCodec.seal(self.envelope,recipient_key=self.key,recipient_key_id="recipient-key")
        self.assertNotIn("hello",json.dumps(packet))
        self.assertEqual(EncryptedEnvelopeCodec.open(packet,recipient_key=self.key,
          expected_workspace_id="ws-a",expected_recipient_entity_id="recipient",expected_key_id="recipient-key"),self.envelope)
    def test_tamper_wrong_key_and_wrong_recipient_fail_closed(self):
        packet=EncryptedEnvelopeCodec.seal(self.envelope,recipient_key=self.key,recipient_key_id="recipient-key")
        altered=dict(packet); altered["ciphertext_b64"]=altered["ciphertext_b64"][:-4]+"AAAA"
        for candidate,key,recipient in ((altered,self.key,"recipient"),(packet,b"x"*32,"recipient"),(packet,self.key,"other")):
            with self.assertRaises(ValueError):
                EncryptedEnvelopeCodec.open(candidate,recipient_key=key,expected_workspace_id="ws-a",
                  expected_recipient_entity_id=recipient,expected_key_id="recipient-key")
    def test_outbox_idempotency_ack_and_delivery(self):
        with tempfile.TemporaryDirectory() as root:
            sent=[]
            box=ReliableDeliveryOutbox(send=lambda packet: sent.append(packet) or {"message_id":"m-1","accepted":True},
              verify_ack=lambda ack,mid: ack.get("message_id")==mid and ack.get("accepted") is True,
              authorize_delivery=lambda ws,mid: True,db_path=f"{root}/outbox.sqlite3")
            self.assertTrue(box.enqueue(workspace_id="ws-a",message_id="m-1",sender_entity_id="sender",encrypted_packet={"x":1})["queued"])
            self.assertTrue(box.enqueue(workspace_id="ws-a",message_id="m-1",sender_entity_id="sender",encrypted_packet={"x":2})["duplicate"])
            self.assertEqual(box.dispatch_one("ws-a","m-1")["status"],"delivered"); self.assertEqual(len(sent),1); box.close()
    def test_retry_dead_letter_revocation_and_quota(self):
        with tempfile.TemporaryDirectory() as root:
            box=ReliableDeliveryOutbox(send=lambda p: (_ for _ in ()).throw(OSError()),
              verify_ack=lambda a,m: False,authorize_delivery=lambda m: True,
              db_path=f"{root}/outbox.sqlite3",max_attempts=1,max_pending=1)
            box.enqueue(workspace_id="ws-a",message_id="m-2",sender_entity_id="sender",encrypted_packet={"x":1})
            with self.assertRaises(ValueError):
                box.enqueue(workspace_id="ws-a",message_id="m-3",sender_entity_id="sender",encrypted_packet={"x":2})
            self.assertEqual(box.dispatch_one("ws-a","m-2")["status"],"dead_letter"); box.close()
        with tempfile.TemporaryDirectory() as root:
            box=ReliableDeliveryOutbox(send=lambda p: {"ok":True},verify_ack=lambda a,m: True,
              authorize_delivery=lambda m: False,db_path=f"{root}/outbox.sqlite3")
            box.enqueue(workspace_id="ws-a",message_id="m-4",sender_entity_id="sender",encrypted_packet={"x":1})
            self.assertEqual(box.dispatch_one("ws-a","m-4")["status"],"revoked"); box.close()
if __name__=="__main__": unittest.main()
