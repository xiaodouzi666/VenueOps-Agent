from __future__ import annotations

from typing import Any

from app.db.mongo import BaseRepository, next_id, utc_now_iso
from app.tools.policies import guard_write

HIGH_IMPACT_ACTIONS = {
    "staff_dispatch",
    "restock_request",
    "signage_instruction",
    "facility_ticket",
    "tenant_campaign",
}


def append_audit(repo: BaseRepository, action_id: str, event: str, actor: str, details: dict[str, Any] | None = None) -> None:
    audit = {
        "_id": next_id("audit", repo.find("action_audit")),
        "action_id": action_id,
        "event": event,
        "actor": actor,
        "details": details or {},
        "created_at": utc_now_iso(),
    }
    repo.insert_one("action_audit", audit)


def create_pending_action(
    repo: BaseRepository,
    *,
    event_id: str,
    action_type: str,
    title: str,
    rationale: str,
    risk_level: str,
    payload: dict[str, Any],
    evidence_doc_ids: list[str],
    data_used: list[str],
    expected_impact: str,
    created_by: str = "venueops_agent",
) -> dict[str, Any]:
    decision = guard_write("actions", "insert", payload)
    if not decision.allowed:
        raise ValueError(decision.reason)
    action = {
        "_id": next_id("action", repo.find("actions")),
        "event_id": event_id,
        "type": action_type,
        "title": title,
        "rationale": rationale,
        "risk_level": risk_level,
        "status": "pending_approval" if action_type in HIGH_IMPACT_ACTIONS else "approved",
        "payload": payload,
        "data_used": data_used,
        "expected_impact": expected_impact,
        "evidence_doc_ids": evidence_doc_ids,
        "created_by": created_by,
        "created_at": utc_now_iso(),
        "approved_by": None,
        "approved_at": None,
        "executed_at": None,
        "audit": [
            {
                "event": "created_pending_approval",
                "actor": created_by,
                "created_at": utc_now_iso(),
                "details": {"requires_human_approval": action_type in HIGH_IMPACT_ACTIONS},
            }
        ],
    }
    repo.insert_one("actions", action)
    append_audit(repo, action["_id"], "created_pending_approval", created_by, {"type": action_type})
    return action


def approve_action(repo: BaseRepository, action_id: str, approver: str = "demo_operator") -> dict[str, Any]:
    action = repo.find_one("actions", {"_id": action_id})
    if not action:
        raise KeyError(f"Action {action_id} not found")
    if action.get("status") == "executed":
        return action
    approved = repo.update_one(
        "actions",
        {"_id": action_id},
        {
            "$set": {
                "status": "approved",
                "approved_by": approver,
                "approved_at": utc_now_iso(),
            },
            "$push": {
                "audit": {
                    "event": "approved",
                    "actor": approver,
                    "created_at": utc_now_iso(),
                    "details": {},
                }
            },
        },
    )
    append_audit(repo, action_id, "approved", approver)
    executed = execute_action(repo, approved or action, approver)
    return executed


def reject_action(repo: BaseRepository, action_id: str, reason: str, actor: str = "demo_operator") -> dict[str, Any]:
    action = repo.update_one(
        "actions",
        {"_id": action_id},
        {
            "$set": {"status": "rejected", "rejection_reason": reason},
            "$push": {
                "audit": {
                    "event": "rejected",
                    "actor": actor,
                    "created_at": utc_now_iso(),
                    "details": {"reason": reason},
                }
            },
        },
    )
    if not action:
        raise KeyError(f"Action {action_id} not found")
    append_audit(repo, action_id, "rejected", actor, {"reason": reason})
    return action


def execute_action(repo: BaseRepository, action: dict[str, Any], actor: str) -> dict[str, Any]:
    action_type = action.get("type")
    payload = action.get("payload", {})
    if action_type == "staff_dispatch":
        _execute_staff_dispatch(repo, action, payload)
    elif action_type == "restock_request":
        _execute_restock_request(repo, action, payload)
    elif action_type == "signage_instruction":
        _execute_signage_instruction(repo, action, payload)
    elif action_type == "facility_ticket":
        _execute_facility_ticket(repo, action, payload)
    elif action_type == "tenant_campaign":
        _execute_tenant_campaign(repo, action, payload)

    executed = repo.update_one(
        "actions",
        {"_id": action["_id"]},
        {
            "$set": {"status": "executed", "executed_at": utc_now_iso()},
            "$push": {
                "audit": {
                    "event": "executed",
                    "actor": actor,
                    "created_at": utc_now_iso(),
                    "details": {"simulated_effect": True},
                }
            },
        },
    )
    append_audit(repo, action["_id"], "executed", actor, {"type": action_type})
    return executed or action


def _execute_staff_dispatch(repo: BaseRepository, action: dict[str, Any], payload: dict[str, Any]) -> None:
    count = int(payload.get("staff_count", 0))
    from_zone = payload.get("from_zone")
    to_zone = payload.get("to_zone")
    moved = 0
    for shift in repo.find("staff_shifts", {"event_id": action["event_id"], "assigned_zone": from_zone, "status": "available"}):
        if moved >= count:
            break
        repo.update_one(
            "staff_shifts",
            {"_id": shift["_id"]},
            {"$set": {"assigned_zone": to_zone, "status": "dispatched", "dispatch_action_id": action["_id"]}},
        )
        moved += 1


def _execute_restock_request(repo: BaseRepository, action: dict[str, Any], payload: dict[str, Any]) -> None:
    inventory_id = payload.get("inventory_id")
    quantity = int(payload.get("quantity", 0))
    item = repo.find_one("inventory", {"_id": inventory_id})
    if item:
        repo.update_one(
            "inventory",
            {"_id": inventory_id},
            {
                "$set": {
                    "current_stock": item.get("current_stock", 0) + quantity,
                    "last_updated": utc_now_iso(),
                    "restock_action_id": action["_id"],
                }
            },
        )


def _execute_signage_instruction(repo: BaseRepository, action: dict[str, Any], payload: dict[str, Any]) -> None:
    repo.insert_one(
        "digital_signage",
        {
            "_id": next_id("signage", repo.find("digital_signage")),
            "event_id": action["event_id"],
            "action_id": action["_id"],
            "status": "scheduled",
            "message": payload.get("message"),
            "target_zones": payload.get("target_zones", []),
            "created_at": utc_now_iso(),
        },
    )


def _execute_facility_ticket(repo: BaseRepository, action: dict[str, Any], payload: dict[str, Any]) -> None:
    incident_id = payload.get("incident_id")
    repo.insert_one(
        "maintenance_tickets",
        {
            "_id": next_id("ticket", repo.find("maintenance_tickets")),
            "event_id": action["event_id"],
            "action_id": action["_id"],
            "incident_id": incident_id,
            "assigned_role": payload.get("assigned_role", "facility"),
            "status": "assigned",
            "created_at": utc_now_iso(),
        },
    )
    if incident_id:
        repo.update_one("incidents", {"_id": incident_id}, {"$set": {"status": "assigned", "assigned_at": utc_now_iso()}})


def _execute_tenant_campaign(repo: BaseRepository, action: dict[str, Any], payload: dict[str, Any]) -> None:
    repo.insert_one(
        "campaign_drafts",
        {
            "_id": next_id("campaign", repo.find("campaign_drafts")),
            "event_id": action["event_id"],
            "action_id": action["_id"],
            "tenant_id": payload.get("tenant_id"),
            "target_zone": payload.get("target_zone"),
            "message": payload.get("message"),
            "status": "drafted",
            "created_at": utc_now_iso(),
        },
    )
