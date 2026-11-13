# XParallel developer conformance examples

This folder contains an illustrative independent entity manifest and protocol examples. The manifest is pending and declares capabilities only; it is not registered, signed, certified or trusted.

The executable local conformance tests are in tests/test_protocol_conformance.py. They demonstrate:
- two independently keyed entities using the same signed-message protocol;
- AES-GCM encrypted packet delivery through the reference Python SDK;
- recipient binding and replay rejection;
- deterministic protocol-version negotiation.

The SDK operates in-process and does not open a network connection. Real federation still requires authenticated TLS transport, trusted key agreement/distribution, registry discovery, approval and policy integration, and multi-node tests.
