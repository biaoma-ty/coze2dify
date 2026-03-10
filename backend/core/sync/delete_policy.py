from __future__ import annotations

from enum import Enum
from typing import Any


DELETE_POLICY_VERSION = "2026-03-10"


class DeleteMode(str, Enum):
    OBSERVE_ONLY = "observe_only"
    APPROVAL_REQUIRED = "approval_required"
    SOFT_DELETE = "soft_delete"


_POLICY_DEFINITIONS: dict[DeleteMode, dict[str, Any]] = {
    DeleteMode.OBSERVE_ONLY: {
        "label": "Observe Only",
        "supported": True,
        "destructive": False,
        "requires_approval": False,
        "summary": "Record delete intent in diff and history only. Leave the Dify app untouched.",
        "rollback_requirement": "No rollback path is required because no delete is executed.",
        "approval_requirement": "None.",
    },
    DeleteMode.APPROVAL_REQUIRED: {
        "label": "Approval Required",
        "supported": True,
        "destructive": False,
        "requires_approval": True,
        "summary": "Record delete intent and block execution until an explicit operator approval workflow exists.",
        "rollback_requirement": "Capture the current Dify app snapshot before any future destructive delete flow is approved.",
        "approval_requirement": "An explicit operator approval artifact must exist before delete execution can be enabled.",
    },
    DeleteMode.SOFT_DELETE: {
        "label": "Soft Delete",
        "supported": False,
        "destructive": True,
        "requires_approval": True,
        "summary": "Reserved for a future archive or tombstone flow. It is intentionally blocked in the current product.",
        "rollback_requirement": "A reversible archive and restore path must exist before soft-delete can be enabled.",
        "approval_requirement": "Approval plus restore automation are mandatory before enablement.",
    },
}

_DELETE_INTENT_STATUS = {
    DeleteMode.OBSERVE_ONLY: "observed",
    DeleteMode.APPROVAL_REQUIRED: "approval_pending",
    DeleteMode.SOFT_DELETE: "blocked",
}


def normalize_delete_mode(mode: str | DeleteMode | None) -> DeleteMode:
    if isinstance(mode, DeleteMode):
        return mode
    try:
        return DeleteMode(str(mode or DeleteMode.OBSERVE_ONLY.value))
    except ValueError:
        return DeleteMode.OBSERVE_ONLY


def ensure_delete_mode_supported(mode: str | DeleteMode | None) -> DeleteMode:
    normalized = normalize_delete_mode(mode)
    if normalized == DeleteMode.SOFT_DELETE:
        raise ValueError(
            "soft_delete is defined but intentionally unsupported until a reversible archive and restore path exists. "
            "Use observe_only or approval_required."
        )
    return normalized


def build_delete_policy(mode: str | DeleteMode | None, *, intent_status: str | None = None) -> dict[str, Any]:
    normalized = normalize_delete_mode(mode)
    policy = {
        "mode": normalized.value,
        "version": DELETE_POLICY_VERSION,
        **_POLICY_DEFINITIONS[normalized],
    }
    if intent_status is not None:
        policy["intent_status"] = intent_status
    return policy


def delete_intent_status(mode: str | DeleteMode | None) -> str:
    return _DELETE_INTENT_STATUS[normalize_delete_mode(mode)]
