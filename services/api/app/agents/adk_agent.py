from __future__ import annotations

from typing import Any

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from app.agents.prompts import ROOT_AGENT_SYSTEM_PROMPT
from app.config import settings
from app.db.mongo import get_repository
from app.tools.action_tools import create_pending_action
from app.tools.risk_tools import compute_incident_priority, compute_inventory_risk, compute_zone_risk, get_current_event_snapshot


def get_current_event_snapshot_tool(event_id: str = "event_wc_demo_001") -> dict[str, Any]:
    """Return the current VenueOps dashboard snapshot from MongoDB."""
    return get_current_event_snapshot(get_repository(), event_id)


def compute_zone_risk_tool(event_id: str = "event_wc_demo_001") -> list[dict[str, Any]]:
    """Return ranked crowd, queue, and staffing risk by venue zone."""
    return compute_zone_risk(get_repository(), event_id)


def compute_inventory_risk_tool(event_id: str = "event_wc_demo_001") -> list[dict[str, Any]]:
    """Return ranked stockout risk by SKU and tenant."""
    return compute_inventory_risk(get_repository(), event_id)


def compute_incident_priority_tool(event_id: str = "event_wc_demo_001") -> list[dict[str, Any]]:
    """Return ranked open incidents with crowd-context priority scores."""
    return compute_incident_priority(get_repository(), event_id)


def create_pending_action_tool(
    title: str,
    action_type: str,
    rationale: str,
    risk_level: str,
    expected_impact: str,
    event_id: str = "event_wc_demo_001",
) -> dict[str, Any]:
    """Create a human-approved operational action proposal.

    This wrapper intentionally keeps payload creation narrow. The production
    FastAPI workflow still owns high-impact execution and audit writes.
    """
    return create_pending_action(
        get_repository(),
        event_id=event_id,
        action_type=action_type,
        title=title,
        rationale=rationale,
        risk_level=risk_level,
        payload={"source": "google_adk_agent", "title": title},
        evidence_doc_ids=[],
        data_used=["google_adk_agent"],
        expected_impact=expected_impact,
        created_by="venueops_adk_agent",
    )


venueops_agent = Agent(
    name="venueops_agent",
    description="Venue operations agent for crowd, retail, incident, and approval workflows.",
    model=settings.gemini_model,
    instruction=ROOT_AGENT_SYSTEM_PROMPT,
    tools=[
        FunctionTool(get_current_event_snapshot_tool),
        FunctionTool(compute_zone_risk_tool),
        FunctionTool(compute_inventory_risk_tool),
        FunctionTool(compute_incident_priority_tool),
        FunctionTool(create_pending_action_tool),
    ],
)
