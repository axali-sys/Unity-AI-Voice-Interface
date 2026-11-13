"""Deterministic XParallel protocol compatibility helpers."""
from __future__ import annotations
import re
_SEMVER=re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

def parse_version(value:str)->tuple[int,int,int]:
    if not isinstance(value,str) or not _SEMVER.fullmatch(value): raise ValueError("invalid_semver")
    return tuple(int(part) for part in value.split("."))

def is_backward_compatible(remote_version:str,minimum_local_version:str)->bool:
    remote,minimum=parse_version(remote_version),parse_version(minimum_local_version)
    return remote[0]==minimum[0] and remote>=minimum

def negotiate_protocol(local_versions:list[str],remote_versions:list[str])->str|None:
    """Choose the highest exact common version; never guess across major versions."""
    if not isinstance(local_versions,list) or not isinstance(remote_versions,list): raise ValueError("protocol_versions_must_be_lists")
    local={v for v in local_versions if isinstance(v,str) and _SEMVER.fullmatch(v)}
    remote={v for v in remote_versions if isinstance(v,str) and _SEMVER.fullmatch(v)}
    common=local&remote
    return max(common,key=parse_version) if common else None
