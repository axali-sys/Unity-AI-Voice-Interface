# Restricted sandbox command profiles

The Docker runner no longer accepts a caller-provided shell command. Execution
payloads may select only a named profile from the host-maintained
`TEST_PROFILES` allowlist. The initial supported profile is
`python-unittest`, mapped to the fixed argument vector:

`python -m unittest discover -v`

The Docker command passes that argument vector directly after the pinned image.
It does not invoke `sh -lc` and does not interpolate payload text into a shell.

Any payload containing the legacy `test_command` field, or an unknown profile,
is blocked before Docker is invoked. Adding a profile requires a code change,
review, tests, and CI—not a free-form request parameter.

This narrows command selection but does not make submitted project files
trustworthy: the approved source code itself remains untrusted and must execute
only inside the isolated sandbox. The current runner remains a development
defense-in-depth boundary, not a hardened multi-tenant microVM.
