# Delete Sync Policy

## Goal

Define how sync should behave when a previously synced Coze workflow disappears from the source system while a mapped Dify app still exists.

Current scope is governance and auditability. No destructive delete is executed by the product today.

## Supported Modes

| Mode | Supported | Runtime Behavior | Approval Requirement | Rollback Requirement |
|------|-----------|------------------|----------------------|----------------------|
| `observe_only` | Yes | Record delete intent in diff preview and sync history. Leave the Dify app untouched. | None | None, because no delete occurs. |
| `approval_required` | Yes | Record delete intent and explicitly block execution until an operator approval workflow exists. Leave the Dify app untouched. | Explicit operator approval artifact required before any future delete execution is enabled. | Capture the current Dify app snapshot before any destructive flow is ever approved. |
| `soft_delete` | No | Intentionally blocked. The API rejects this mode today. | Would require approval plus a reversible archive or tombstone workflow. | A tested archive and restore path must exist before enablement. |

## Representation In Product Surfaces

- Sync config persists `delete_mode` and returns a structured `delete_policy` payload.
- `POST /sync/diff` returns the active `delete_policy` at the top level.
- Delete-gap items in diff output and sync history include `delete_policy.intent_status`:
  - `observed` for `observe_only`
  - `approval_pending` for `approval_required`
  - `blocked` for any future unsupported destructive mode
- Sync history audit stores the configured delete policy alongside source and target database references.

## Safety Rules

- The product does not delete or archive Dify apps automatically.
- Delete gaps continue to appear as non-success outcomes in sync summaries so operators must review them.
- Destructive delete support cannot be added without:
  - explicit operator approval capture
  - persisted target snapshot or equivalent rollback artifact
  - documented restore procedure
  - audit trail proving who approved and when execution occurred

## Rollout Decision

`observe_only` remains the default.

`approval_required` is supported as a governance mode for teams that want delete intent recorded with stronger process language, but it still performs no destructive action.

`soft_delete` remains intentionally unsupported until rollback and restore guarantees are implemented end to end.
