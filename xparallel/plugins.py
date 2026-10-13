"""Plugin catalog and capability gates for the Axaliai Universal AI Mixer.

This module advertises integration status honestly. A configured credential does not
mean a connector is implemented or authorized; execution adapters must be registered
explicitly before a plugin can run.
"""
from __future__ import annotations

import os
from typing import Any

PLUGIN_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "web_search",
        "name": "Web search",
        "kind": "tool",
        "purpose": "Retrieve current public information",
        "credential_env": "XP_WEB_SEARCH_API_KEY",
        "adapter": "web_search",
        "permissions": ["search_public_web"],
        "approval_required": False,
    },
    {
        "id": "github",
        "name": "GitHub",
        "kind": "connected_app",
        "purpose": "Inspect repositories, issues, pull requests, and workflows",
        "credential_env": "GITHUB_TOKEN",
        "adapter": "github",
        "permissions": ["repository_read"],
        "approval_required": True,
    },
    {
        "id": "google_drive",
        "name": "Google Drive",
        "kind": "connected_app",
        "purpose": "Search and retrieve files the user has authorized",
        "credential_env": "GOOGLE_DRIVE_ACCESS_TOKEN",
        "adapter": "google_drive",
        "permissions": ["drive_file_read"],
        "approval_required": True,
    },
    {
        "id": "file_retrieval",
        "name": "File retrieval",
        "kind": "tool",
        "purpose": "Retrieve content from configured, authorized file sources",
        "credential_env": "",
        "adapter": "file_retrieval",
        "permissions": ["read_authorized_files"],
        "approval_required": False,
    },
    {
        "id": "ai_memory",
        "name": "AI Memory",
        "kind": "tool",
        "purpose": "Retrieve relevant saved context without treating it as instructions",
        "credential_env": "",
        "adapter": "ai_memory",
        "permissions": ["read_authorized_memory"],
        "approval_required": False,
    },
    {
        "id": "xparallel_sandbox",
        "name": "XParallel isolated sandbox",
        "kind": "tool",
        "purpose": "Test code and programs in an isolated environment",
        "credential_env": "",
        "adapter": "xparallel_sandbox",
        "permissions": ["sandbox_test"],
        "approval_required": True,
    },
]

# No adapters are enabled by this catalog alone. Register only after a real,
# reviewed implementation has been added and tested.
IMPLEMENTED_ADAPTERS: set[str] = set()


def plugin_catalog(sandbox_available: bool = False) -> dict[str, Any]:
    plugins = []
    for item in PLUGIN_REGISTRY:
        plugin = dict(item)
        env_name = plugin.pop("credential_env")
        configured = bool(env_name and os.getenv(env_name, "").strip())
        adapter_ready = plugin["adapter"] in IMPLEMENTED_ADAPTERS
        if plugin["id"] == "xparallel_sandbox":
            adapter_ready = bool(sandbox_available)
        if adapter_ready and (configured or not env_name):
            status = "available"
        elif env_name and not configured:
            status = "credentials_missing"
        else:
            status = "adapter_not_implemented"
        plugin["configured"] = configured
        plugin["status"] = status
        plugin["can_execute"] = status == "available"
        plugins.append(plugin)
    return {
        "service": "Axaliai Universal AI Mixer",
        "state": "catalog_only" if not any(p["can_execute"] for p in plugins) else "partial",
        "plugins": plugins,
        "security": {
            "credentials_from_environment_only": True,
            "least_privilege": True,
            "approval_required_for_consequential_actions": True,
            "catalog_does_not_grant_execution_permission": True,
        },
    }


def execute_plugin(plugin_id: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Fail closed until a reviewed adapter and authorization path are implemented."""
    known = next((p for p in PLUGIN_REGISTRY if p["id"] == plugin_id), None)
    if not known:
        return {"state": "plugin_not_found", "plugin_id": plugin_id}
    if known["adapter"] not in IMPLEMENTED_ADAPTERS:
        return {
            "state": "plugin_unavailable",
            "plugin_id": plugin_id,
            "reason": "adapter_not_implemented",
            "action": action,
        }
    # Adapter dispatch intentionally remains fail-closed until adapters are registered.
    return {
        "state": "plugin_unavailable",
        "plugin_id": plugin_id,
        "reason": "execution_adapter_not_registered",
        "action": action,
    }
