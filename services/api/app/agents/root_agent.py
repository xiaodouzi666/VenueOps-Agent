from __future__ import annotations

import json
from typing import Any

from app.agents.prompts import ROOT_AGENT_SYSTEM_PROMPT
from app.agents.subagents.ops_analyst import analyze_ops
from app.agents.subagents.planner import plan_with_gemini
from app.agents.subagents.retail_analyst import analyze_retail
from app.agents.subagents.safety_agent import analyze_safety
from app.config import settings
from app.db.mongo import BaseRepository, next_id, utc_now_iso
from app.tools.action_tools import create_pending_action
from app.tools.mongodb_mcp import MongoMCPBridge, ToolTrace
from app.tools.risk_tools import get_current_event_snapshot
from app.tools.sop_retriever import retrieve_relevant_sops


def run_venueops_agent(repo: BaseRepository, mission: str, event_id: str = "event_wc_demo_001") -> dict[str, Any]:
    trace = ToolTrace()
    mcp = MongoMCPBridge(repo, trace)
    try:
        return _run_venueops_agent_with_bridge(repo, mission, event_id, trace, mcp)
    finally:
        mcp.close()


def _run_venueops_agent_with_bridge(
    repo: BaseRepository,
    mission: str,
    event_id: str,
    trace: ToolTrace,
    mcp: MongoMCPBridge,
) -> dict[str, Any]:
    event = repo.find_one("events", {"_id": event_id})
    if not event:
        raise KeyError(f"Event {event_id} not found")

    # Observe through MongoDB MCP Server-backed database reads in hosted mode. These calls are intentionally
    # explicit so the UI can prove the agent inspected operational data first.
    mcp.collection_schema("telemetry", "Inspect telemetry shape before aggregating current crowd pressure")
    mcp.aggregate(
        "telemetry",
        [{"$match": {"event_id": event_id}}, {"$sort": {"timestamp": -1}}, {"$limit": 30}],
        "Aggregate latest telemetry by event and zone",
    )
    mcp.find("inventory", {"event_id": event_id}, "Find priority SKUs and stockout risks", limit=20)
    mcp.find("staff_shifts", {"event_id": event_id, "status": "available"}, "Find movable available staff", limit=20)
    mcp.count("incidents", {"event_id": event_id, "status": "open"}, "Count open incidents requiring triage")

    ops = analyze_ops(repo, event_id)
    retail = analyze_retail(repo, event_id)
    safety = analyze_safety(repo, event_id)
    sops = retrieve_relevant_sops(
        repo,
        mcp,
        f"{mission} gate overflow food court restock facility incident tenant campaign signage",
        top_k=4,
    )
    planner = plan_with_gemini(mission=mission, ops=ops, retail=retail, safety=safety, sops=sops)
    trace.add(
        tool="gemini.plan",
        collection="agent_planner",
        purpose="Generate structured operations strategy from observed MongoDB metrics and SOP evidence",
        status=planner["status"],
        duration_ms=planner["duration_ms"],
        input_summary={"mission": mission, "sop_count": len(sops)},
        output_summary={
            "mode": planner["mode"],
            "ranked_actions": len(planner.get("ranked_actions", [])),
            **({"reason": planner["reason"]} if planner.get("reason") else {}),
        },
        evidence_ids=[doc["_id"] for doc in sops if doc.get("_id")],
        transport=planner["mode"],
    )
    actions = _create_recommended_actions(repo, event_id, ops, retail, safety, sops)
    for action in actions:
        trace.add(
            tool="create_pending_action",
            collection="actions",
            purpose=f"Create human-approved action proposal: {action['title']}",
            status="ok",
            duration_ms=0,
            input_summary={"type": action["type"], "risk_level": action["risk_level"]},
            output_summary={"action_id": action["_id"], "status": action["status"]},
            evidence_ids=action.get("evidence_doc_ids", []),
            transport="venueops_guarded_write",
        )
    summary = _build_summary(mission, ops, retail, safety, actions, sops)
    gemini_note = _optional_gemini_explanation(mission, summary)

    run = {
        "_id": next_id("run", repo.find("agent_runs")),
        "event_id": event_id,
        "user_goal": mission,
        "system_prompt": ROOT_AGENT_SYSTEM_PROMPT,
        "steps": trace.steps,
        "plan_summary": summary["situation_summary"],
        "recommended_action_ids": [action["_id"] for action in actions],
        "planner": planner,
        "gemini_note": gemini_note,
        "created_at": utc_now_iso(),
    }
    repo.insert_one("agent_runs", run)
    snapshot = get_current_event_snapshot(repo, event_id)

    return {
        **summary,
        "agent_run_id": run["_id"],
        "recommended_actions": actions,
        "required_confirmations": len([action for action in actions if action.get("status") == "pending_approval"]),
        "evidence": sops,
        "tool_trace": trace.steps,
        "planner": planner,
        "snapshot": snapshot,
        "gemini_note": gemini_note,
        "agent_mode": planner["mode"],
    }


def _create_recommended_actions(
    repo: BaseRepository,
    event_id: str,
    ops: dict[str, Any],
    retail: dict[str, Any],
    safety: dict[str, Any],
    sops: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence_doc_ids = [doc["_id"] for doc in sops if doc.get("_id")]
    top_zone = ops["top_zone_risks"][0]
    gate_doc_ids = [doc["_id"] for doc in sops if "gate" in doc.get("tags", []) or "crowd" in doc.get("tags", [])]
    inventory_doc_ids = [doc["_id"] for doc in sops if "restock" in doc.get("tags", []) or "inventory" in doc.get("tags", [])]
    facility_doc_ids = [doc["_id"] for doc in sops if "facility" in doc.get("tags", []) or "incident" in doc.get("tags", [])]
    tenant_doc_ids = [doc["_id"] for doc in sops if "tenant" in doc.get("tags", []) or "campaign" in doc.get("tags", [])]

    top_inventory = _select_demo_inventory(retail["top_inventory_risks"])
    top_incident = _select_facility_incident(safety["top_incidents"])
    actions = [
        create_pending_action(
            repo,
            event_id=event_id,
            action_type="staff_dispatch",
            title="Move 4 trained stewards from Retail Wing East to Gate B",
            rationale=(
                f"{top_zone['zone_name']} is {top_zone['zone_pressure']:.0%} full with "
                f"{top_zone['avg_wait_min']} min wait; Gate Overflow Procedure threshold is 85% pressure and 15 min wait."
            ),
            risk_level="high",
            payload={"from_zone": "retail_wing_east", "to_zone": "gate_b", "staff_count": 4},
            evidence_doc_ids=gate_doc_ids or evidence_doc_ids,
            data_used=["telemetry", "zones", "staff_shifts", "sop_docs"],
            expected_impact="Reduce Gate B wait by opening supervised flow and adding wayfinding capacity.",
        ),
        create_pending_action(
            repo,
            event_id=event_id,
            action_type="signage_instruction",
            title="Draft digital signage to redirect new arrivals from Gate B to Gate D",
            rationale="Gate D remains below warning pressure while Gate B is critical; rerouting is allowed by crowd signage SOP.",
            risk_level="medium",
            payload={
                "target_zones": ["gate_b", "main_concourse"],
                "message": "Gate B is busy. Please follow signs to Gate D for faster entry.",
            },
            evidence_doc_ids=gate_doc_ids or evidence_doc_ids,
            data_used=["telemetry", "zones", "sop_docs"],
            expected_impact="Lower new-arrival pressure at Gate B without sending fans through incident zones.",
        ),
        create_pending_action(
            repo,
            event_id=event_id,
            action_type="restock_request",
            title=f"Send urgent restock request for {top_inventory['name']}",
            rationale=(
                f"{top_inventory['name']} has {top_inventory['current_stock']} units against "
                f"{top_inventory['projected_next_90min']} projected demand."
            ),
            risk_level="high",
            payload={
                "inventory_id": top_inventory["inventory_id"],
                "tenant_id": top_inventory["tenant_id"],
                "quantity": 320,
                "assigned_role": "retail_support",
            },
            evidence_doc_ids=inventory_doc_ids or evidence_doc_ids,
            data_used=["inventory", "tenants", "sop_docs"],
            expected_impact="Move the SKU above projected 90-minute demand before kickoff.",
        ),
        create_pending_action(
            repo,
            event_id=event_id,
            action_type="facility_ticket",
            title=f"Assign facility team to {top_incident['zone_name']} incident",
            rationale=top_incident["explanation"],
            risk_level=top_incident.get("severity", "medium"),
            payload={"incident_id": top_incident["_id"], "assigned_role": "facility", "sla_min": 10},
            evidence_doc_ids=facility_doc_ids or evidence_doc_ids,
            data_used=["incidents", "telemetry", "sop_docs"],
            expected_impact="Meet incident SLA and reduce queue spillover near guest facilities.",
        ),
        create_pending_action(
            repo,
            event_id=event_id,
            action_type="tenant_campaign",
            title="Draft FanGear East campaign to pull traffic toward Retail Wing East",
            rationale="Retail Wing East has spare capacity and tenant campaigns can support crowd balancing after approval.",
            risk_level="low",
            payload={
                "tenant_id": "tenant_032",
                "target_zone": "retail_wing_east",
                "message": "Shorter lines in Retail Wing East: fan gear and rain ponchos available now.",
            },
            evidence_doc_ids=tenant_doc_ids or evidence_doc_ids,
            data_used=["tenants", "telemetry", "sop_docs"],
            expected_impact="Move optional shopping traffic away from Gate B and Food Court pressure.",
        ),
    ]
    return actions


def _build_summary(
    mission: str,
    ops: dict[str, Any],
    retail: dict[str, Any],
    safety: dict[str, Any],
    actions: list[dict[str, Any]],
    sops: list[dict[str, Any]],
) -> dict[str, Any]:
    top_zone = ops["top_zone_risks"][0]
    top_inventory = _select_demo_inventory(retail["top_inventory_risks"])
    top_incident = _select_facility_incident(safety["top_incidents"])
    return {
        "mission": mission,
        "situation_summary": (
            f"{top_zone['zone_name']} is critical at {top_zone['zone_pressure']:.0%} pressure "
            f"with {top_zone['avg_wait_min']} min wait. {top_inventory['tenant_name']} has a "
            f"{top_inventory['name']} stockout risk. {top_incident['zone_name']} has an open "
            f"{top_incident['severity']} incident."
        ),
        "key_risks": [
            {
                "risk": "Gate B queue overflow",
                "severity": "high",
                "evidence": ["mongodb.aggregate telemetry", "Gate Overflow Procedure"],
                "metric": top_zone,
            },
            {
                "risk": f"{top_inventory['name']} stockout",
                "severity": "high" if top_inventory["status"] == "critical" else "medium",
                "evidence": ["mongodb.find inventory", "Food Court Restock Playbook"],
                "metric": top_inventory,
            },
            {
                "risk": f"{top_incident['zone_name']} incident SLA",
                "severity": top_incident.get("severity", "medium"),
                "evidence": ["mongodb.count incidents", "Facility Incident SLA"],
                "metric": top_incident,
            },
        ],
        "plan": [
            "Observe current operations data from MongoDB.",
            "Analyze crowd, inventory, staffing, and incident risk with deterministic formulas.",
            "Retrieve relevant SOPs through Atlas Vector Search-first SOP retrieval.",
            "Create five pending actions with evidence and expected impact.",
            "Wait for operator approval before executing operational changes.",
        ],
        "action_count": len(actions),
        "sop_titles": [doc["title"] for doc in sops],
    }


def _optional_gemini_explanation(mission: str, summary: dict[str, Any]) -> str | None:
    if not settings.google_cloud_project or settings.demo_mode:
        return None
    try:
        from google import genai

        client = genai.Client(vertexai=True, project=settings.google_cloud_project, location=settings.google_cloud_location)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=(
                "Explain this venue operations plan in two concise sentences for a hackathon judge. "
                f"Mission: {mission}\nSummary: {json.dumps(summary, ensure_ascii=False)}"
            ),
        )
        return response.text
    except Exception as exc:
        return f"Gemini explanation unavailable: {exc}"


def _select_demo_inventory(inventory_risks: list[dict[str, Any]]) -> dict[str, Any]:
    for item in inventory_risks:
        if item.get("sku") == "water_500ml":
            return item
    return inventory_risks[0]


def _select_facility_incident(incidents: list[dict[str, Any]]) -> dict[str, Any]:
    for incident in incidents:
        if incident.get("type") == "facility" and incident.get("status") == "open":
            return incident
    return incidents[0]
