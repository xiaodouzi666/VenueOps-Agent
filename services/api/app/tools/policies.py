from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings

READ_COLLECTIONS = {
    "venues",
    "events",
    "zones",
    "telemetry",
    "tenants",
    "inventory",
    "staff_shifts",
    "incidents",
    "sop_docs",
    "actions",
    "agent_runs",
}

WRITE_COLLECTIONS = {
    "actions",
    "agent_runs",
    "action_audit",
    "telemetry",
    "staff_shifts",
    "inventory",
    "incidents",
    "digital_signage",
    "maintenance_tickets",
    "campaign_drafts",
}

BLOCKED_OPERATIONS = {"drop", "delete", "delete_many", "delete_one", "replace_many"}


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def guard_database(database: str | None) -> PolicyDecision:
    if database and database != settings.allowed_db:
        return PolicyDecision(False, f"Database {database} is outside allowed scope {settings.allowed_db}.")
    return PolicyDecision(True, "Database allowed.")


def guard_read(collection: str, limit: int | None = None) -> PolicyDecision:
    if collection not in READ_COLLECTIONS:
        return PolicyDecision(False, f"Collection {collection} is not read-allowlisted.")
    if limit is not None and limit > settings.max_query_limit:
        return PolicyDecision(False, f"Limit {limit} exceeds max {settings.max_query_limit}.")
    return PolicyDecision(True, "Read allowed.")


def guard_write(collection: str, operation: str, payload: dict[str, Any] | None = None) -> PolicyDecision:
    if operation in BLOCKED_OPERATIONS:
        return PolicyDecision(False, f"Operation {operation} is destructive and blocked.")
    if collection not in WRITE_COLLECTIONS:
        return PolicyDecision(False, f"Collection {collection} is not write-allowlisted.")
    payload = payload or {}
    if "drop" in str(payload).lower() or "delete" in str(payload).lower():
        return PolicyDecision(False, "Payload contains a blocked destructive verb.")
    return PolicyDecision(True, "Write allowed.")
