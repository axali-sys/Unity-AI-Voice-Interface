# XParallel Security Integration V1

This layer connects the production security foundation to the API.

- Security-sensitive API actions are authorized by explicit role/action policy.
- Audit events are persisted in the same local SQLite store used by the V1 repository.
- Private requests use the authenticated bearer-token context; the client cannot choose its role.
- XP_DEFAULT_ROLE controls the role assigned to that authenticated application identity (default: owner for the current single-operator V1).
- Public endpoints remain origin/rate-limit protected and are not granted deployment approval.
- Production deployment should replace the single application identity with a real identity provider and organization membership service.

No credentials, payment details, or automatic transfers are stored in source control.
