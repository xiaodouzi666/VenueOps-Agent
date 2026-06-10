from __future__ import annotations

import json
import re
import time
from typing import Any

from app.config import settings


def plan_with_gemini(
    *,
    mission: str,
    ops: dict[str, Any],
    retail: dict[str, Any],
    safety: dict[str, Any],
    sops: list[dict[str, Any]],
) -> dict[str, Any]:
    """Ask Gemini for a compact operations strategy, then validate locally.

    Gemini is used as the planner when Vertex configuration is present. The
    returned strategy is advisory: local deterministic tools still compute
    risk, apply guardrails, and create the actual pending actions.
    """

    started = time.perf_counter()
    fallback = _fallback_strategy(mission, ops, retail, safety, sops)
    if not settings.google_cloud_project or settings.demo_mode:
        return {
            **fallback,
            "status": "skipped",
            "mode": "deterministic_fallback",
            "reason": "Vertex/Gemini planner is disabled until GOOGLE_CLOUD_PROJECT is set and demo mode is false.",
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }

    try:
        from google import genai

        client = genai.Client(
            vertexai=settings.google_genai_use_vertexai,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_planner_prompt(mission, ops, retail, safety, sops),
        )
        raw_text = response.text or ""
        parsed = _extract_json_object(raw_text)
        ranked_actions = _ranked_actions(parsed) or fallback["ranked_actions"]
        constraints = _string_list(parsed.get("constraints")) or fallback["constraints"]
        verification_focus = _string_list(parsed.get("verification_focus")) or fallback["verification_focus"]
        return {
            "status": "ok",
            "mode": "gemini_vertex_planner",
            "model": settings.gemini_model,
            "summary": str(parsed.get("summary") or fallback["summary"])[:600],
            "ranked_actions": ranked_actions[:6],
            "constraints": constraints[:6],
            "verification_focus": verification_focus[:6],
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:
        return {
            **fallback,
            "status": "fallback",
            "mode": "deterministic_fallback",
            "reason": f"Gemini planner unavailable: {exc}",
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }


def _planner_prompt(
    mission: str,
    ops: dict[str, Any],
    retail: dict[str, Any],
    safety: dict[str, Any],
    sops: list[dict[str, Any]],
) -> str:
    context = {
        "mission": mission,
        "top_zone_risks": ops.get("top_zone_risks", [])[:4],
        "top_inventory_risks": retail.get("top_inventory_risks", [])[:4],
        "top_incidents": safety.get("top_incidents", [])[:4],
        "sop_evidence": [
            {
                "_id": doc.get("_id"),
                "title": doc.get("title"),
                "tags": doc.get("tags", []),
                "score": doc.get("score"),
            }
            for doc in sops[:4]
        ],
    }
    return (
        "You are the Planner Agent inside VenueOps Agent. Use only the JSON context below. "
        "Create a venue operations strategy that must still require human approval for operational actions. "
        "Return JSON only with keys: summary, ranked_actions, constraints, verification_focus. "
        "Each ranked_actions item must have type, title, rationale, risk_level, and evidence_doc_ids. "
        f"Context: {json.dumps(context, ensure_ascii=False)}"
    )


def _fallback_strategy(
    mission: str,
    ops: dict[str, Any],
    retail: dict[str, Any],
    safety: dict[str, Any],
    sops: list[dict[str, Any]],
) -> dict[str, Any]:
    top_zone = (ops.get("top_zone_risks") or [{}])[0]
    top_inventory = (retail.get("top_inventory_risks") or [{}])[0]
    top_incident = (safety.get("top_incidents") or [{}])[0]
    evidence_ids = [doc.get("_id") for doc in sops if doc.get("_id")]
    return {
        "summary": (
            f"Plan for {mission}: prioritize crowd flow at {top_zone.get('zone_name', 'the riskiest zone')}, "
            f"protect stock availability for {top_inventory.get('name', 'priority SKUs')}, and keep "
            f"{top_incident.get('zone_name', 'facility incidents')} within SLA."
        ),
        "ranked_actions": [
            {
                "type": "staff_dispatch",
                "title": "Move trained stewards to the highest-risk gate",
                "rationale": "Crowd pressure and wait time exceed SOP thresholds.",
                "risk_level": "high",
                "evidence_doc_ids": evidence_ids,
            },
            {
                "type": "signage_instruction",
                "title": "Draft directional signage for safer arrivals",
                "rationale": "Low-pressure neighboring zones can absorb arrivals after approval.",
                "risk_level": "medium",
                "evidence_doc_ids": evidence_ids,
            },
            {
                "type": "restock_request",
                "title": "Prepare urgent restock for priority inventory",
                "rationale": "Projected demand exceeds current stock.",
                "risk_level": "high",
                "evidence_doc_ids": evidence_ids,
            },
            {
                "type": "facility_ticket",
                "title": "Assign facility response to the top open incident",
                "rationale": "Open incidents near pressured zones increase SLA and safety risk.",
                "risk_level": "medium",
                "evidence_doc_ids": evidence_ids,
            },
            {
                "type": "tenant_campaign",
                "title": "Draft tenant campaign to rebalance optional traffic",
                "rationale": "Retail capacity can help pull traffic away from congestion.",
                "risk_level": "low",
                "evidence_doc_ids": evidence_ids,
            },
        ],
        "constraints": [
            "Use current MongoDB operational data only.",
            "Keep every operationally meaningful action pending until an operator approves it.",
            "Do not perform destructive database operations.",
        ],
        "verification_focus": [
            "Recheck pressure and wait time after approved staff or signage actions.",
            "Recheck inventory risk after approved restock actions.",
            "Confirm action audit events are written for approval, execution, and rejection.",
        ],
    }


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Planner response was not a JSON object.")
    return parsed


def _ranked_actions(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    actions = parsed.get("ranked_actions")
    if not isinstance(actions, list):
        return []
    cleaned: list[dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        cleaned.append(
            {
                "type": str(action.get("type", ""))[:80],
                "title": str(action.get("title", ""))[:180],
                "rationale": str(action.get("rationale", ""))[:500],
                "risk_level": str(action.get("risk_level", "medium"))[:40],
                "evidence_doc_ids": [
                    str(item) for item in action.get("evidence_doc_ids", []) if isinstance(item, str)
                ][:8],
            }
        )
    return cleaned


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item)[:300] for item in value if isinstance(item, str)]
