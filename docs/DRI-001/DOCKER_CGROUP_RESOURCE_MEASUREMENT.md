# Docker Linux cgroup v2 resource measurement

`xparallel/docker_cgroup_meter.py` adds a host-side measurement adapter that
resolves the Docker container's init PID, reads its unified cgroup v2 path from
host `/proc/<pid>/cgroup`, and reads kernel-maintained `cpu.stat`,
`memory.peak`, and `pids.peak` counters.

It rejects invalid container IDs, cgroup v1, missing samples, path escapes,
unavailable counters, and malformed output sizes. It reports CPU milliseconds
from cgroup `usage_usec`, peak memory in MiB, peak PIDs, elapsed wall time and
the caller-supplied byte count of captured stdout/stderr.

## Integration requirement

The runner must keep the Docker container present until the final cgroup
counters are read, write its container ID to a host-only cidfile, sample while
the container is alive, then remove the container. The meter must run on the
Linux Docker host with read access to host `/proc` and cgroup v2 files. This
is not available from a remote Docker daemon unless a trusted host-side agent
runs the meter there.

The module and unit tests do not prove a live Docker daemon or production host
configuration. Do not enable the execution API until this adapter is wired to
the actual worker lifecycle and tested on the target host.
