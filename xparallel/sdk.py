"""Small Python SDK for signing and encrypting XParallel entity messages."""
from __future__ import annotations
from typing import Any,Callable
from xparallel.entity_messaging import EntityMessageService
from xparallel.secure_transport import EncryptedEnvelopeCodec

class XParallelEntitySDK:
    """Reference SDK. It creates/opens packets but does not perform network delivery."""
    def __init__(self,*,workspace_id:str,entity_id:str,key_id:str,private_key:Any,
        message_service:EntityMessageService,
        resolve_recipient_key:Callable[[str,str],dict[str,Any]]):
        for name,value in (("workspace_id",workspace_id),("entity_id",entity_id),("key_id",key_id)):
            if not isinstance(value,str) or not value.strip() or len(value)>200: raise ValueError(f"invalid_{name}")
        if not hasattr(private_key,"sign"): raise TypeError("ed25519_private_key_required")
        if not isinstance(message_service,EntityMessageService) or not callable(resolve_recipient_key):
            raise TypeError("message_service_and_recipient_key_resolver_required")
        self.workspace_id,self.entity_id,self.key_id=workspace_id,entity_id,key_id
        self._private,self._messages,self._resolve=private_key,message_service,resolve_recipient_key

    def create_packet(self,*,recipient_entity_id:str,message_type:str,body:Any,ttl_seconds:int=300)->dict[str,Any]:
        envelope=self._messages.create_message(self.workspace_id,self.entity_id,self.key_id,
            recipient_entity_id,message_type,body,self._private,ttl_seconds)
        recipient=self._resolve(self.workspace_id,recipient_entity_id)
        if not isinstance(recipient,dict) or not isinstance(recipient.get("key_id"),str):
            raise LookupError("recipient_encryption_key_unavailable")
        packet=EncryptedEnvelopeCodec.seal(envelope,recipient_key=recipient.get("key"),
            recipient_key_id=recipient["key_id"])
        return packet

    def receive_packet(self,packet:dict[str,Any],*,recipient_key_id:str,recipient_key:bytes)->dict[str,Any]:
        envelope=EncryptedEnvelopeCodec.open(packet,recipient_key=recipient_key,
            expected_workspace_id=self.workspace_id,expected_recipient_entity_id=self.entity_id,
            expected_key_id=recipient_key_id)
        return self._messages.verify_and_accept(envelope,self.workspace_id,self.entity_id)
