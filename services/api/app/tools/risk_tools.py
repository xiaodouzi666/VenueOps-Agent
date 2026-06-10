from __future__ import annotations

import math
from typing import Any

from app.db.mongo import BaseRepository

WAIT_SLA_MIN = 15
QUEUE_THRESHOLD_RATIO = 0.18


def latest_telemetry_by_zone(repo: BaseRepository, event_id: str) -> dict[str, dict[str, Any]]:
    rows = repo.find("telemetry", {"event_id": event_id})
    latest: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: item.get("timestamp", "")):
        latest[row["zone_id"]] = row
    return latest


def compute_zone_risk(repo: BaseRepository, event_id: str) -> list[dict[str, Any]]:
    zones = {zone["_id"]: zone for zone in repo.find("zones")}
    latest = latest_telemetry_by_zone(repo, event_id)
    staff = repo.find("staff_shifts", {"event_id": event_id})
    available_by_zone: dict[str, int] = {}
    for shift in staff:
        if shift.get("status") in {"available", "dispatched"}:
            available_by_zone[shift.get("assigned_zone", "")] = available_by_zone.get(shift.get("assigned_zone", ""), 0) + 1

    risks: list[dict[str, Any]] = []
    for zone_id, telemetry in latest.items():
        zone = zones.get(zone_id)
        if not zone:
            continue
        safe_capacity = max(zone.get("safe_capacity", 1), 1)
        people_count = telemetry.get("people_count", 0)
        queue_length = telemetry.get("queue_length", 0)
        avg_wait_min = telemetry.get("avg_wait_min", 0)
        pressure = people_count / safe_capacity
        queue_threshold = max(safe_capacity * QUEUE_THRESHOLD_RATIO, 1)
        queue_risk = max(avg_wait_min / WAIT_SLA_MIN, queue_length / queue_threshold)
        event_multiplier = 1.15
        required_staff = math.ceil(max(pressure, 0.35) * zone.get("default_staff_required", 1) * event_multiplier)
        available_staff = available_by_zone.get(zone_id, 0)
        staffing_gap = max(required_staff - available_staff, 0)
        staffing_gap_risk = min(staffing_gap / max(required_staff, 1), 1)
        confidence = telemetry.get("sensor_confidence", 0.8)
        safety_risk = min(max(pressure, queue_risk), 1.5)
        entrance_boost = 0.08 if zone.get("type") == "entrance" and (pressure >= 0.9 or avg_wait_min >= 15) else 0
        priority_score = (
            0.35 * min(safety_risk, 1)
            + 0.25 * min(queue_risk, 1)
            + 0.10 * staffing_gap_risk
            + 0.10 * confidence
            + entrance_boost
        )
        status = "normal"
        if pressure >= zone.get("critical_threshold", 0.9) or avg_wait_min >= 15:
            status = "critical"
        elif pressure >= zone.get("warning_threshold", 0.75) or avg_wait_min >= 10:
            status = "warning"
        risks.append(
            {
                "zone_id": zone_id,
                "zone_name": zone.get("name", zone_id),
                "zone_type": zone.get("type"),
                "people_count": people_count,
                "safe_capacity": safe_capacity,
                "zone_pressure": round(pressure, 3),
                "queue_length": queue_length,
                "avg_wait_min": avg_wait_min,
                "queue_risk": round(queue_risk, 3),
                "required_staff": required_staff,
                "available_staff": available_staff,
                "staffing_gap": staffing_gap,
                "sensor_confidence": confidence,
                "priority_score": round(priority_score, 3),
                "status": status,
                "map": zone.get("map"),
                "neighbors": zone.get("neighbors", []),
                "source_collections": ["zones", "telemetry", "staff_shifts"],
                "explanation": (
                    f"{zone.get('name', zone_id)} pressure is {pressure:.0%}, "
                    f"wait is {avg_wait_min} min, staffing gap is {staffing_gap}."
                ),
            }
        )
    return sorted(risks, key=lambda row: row["priority_score"], reverse=True)


def compute_inventory_risk(repo: BaseRepository, event_id: str) -> list[dict[str, Any]]:
    tenants = {tenant["_id"]: tenant for tenant in repo.find("tenants")}
    risks: list[dict[str, Any]] = []
    for item in repo.find("inventory", {"event_id": event_id}):
        stock = max(item.get("current_stock", 0), 1)
        projected = item.get("projected_next_90min", 0)
        ratio = projected / stock
        status = "normal"
        if ratio >= 1.5 or item.get("current_stock", 0) < item.get("reorder_threshold", 0):
            status = "critical"
        elif ratio >= 1:
            status = "warning"
        tenant = tenants.get(item.get("tenant_id"), {})
        risks.append(
            {
                "inventory_id": item["_id"],
                "tenant_id": item.get("tenant_id"),
                "tenant_name": tenant.get("name", item.get("tenant_id")),
                "zone_id": tenant.get("zone_id"),
                "sku": item.get("sku"),
                "name": item.get("name"),
                "current_stock": item.get("current_stock", 0),
                "reorder_threshold": item.get("reorder_threshold", 0),
                "projected_next_90min": projected,
                "stockout_risk": round(ratio, 3),
                "status": status,
                "source_collections": ["inventory", "tenants"],
                "explanation": (
                    f"{item.get('name')} has {item.get('current_stock')} units against "
                    f"{projected} projected demand in the next 90 minutes."
                ),
            }
        )
    return sorted(risks, key=lambda row: row["stockout_risk"], reverse=True)


def compute_incident_priority(repo: BaseRepository, event_id: str) -> list[dict[str, Any]]:
    severity_weight = {"low": 0.35, "medium": 0.7, "high": 1.0, "critical": 1.25}
    zone_risks = {risk["zone_id"]: risk for risk in compute_zone_risk(repo, event_id)}
    incidents: list[dict[str, Any]] = []
    for incident in repo.find("incidents", {"event_id": event_id}):
        if incident.get("status") not in {"open", "monitoring", "assigned"}:
            continue
        zone = zone_risks.get(incident.get("zone_id"), {})
        zone_multiplier = 1 + min(zone.get("zone_pressure", 0), 1)
        priority = severity_weight.get(incident.get("severity", "low"), 0.35) * zone_multiplier * 1.15
        incidents.append(
            {
                **incident,
                "priority_score": round(priority, 3),
                "zone_pressure": zone.get("zone_pressure", 0),
                "zone_name": zone.get("zone_name", incident.get("zone_id")),
                "source_collections": ["incidents", "telemetry", "zones"],
                "explanation": (
                    f"{incident.get('severity', 'low').title()} {incident.get('type')} incident in "
                    f"{zone.get('zone_name', incident.get('zone_id'))} with zone pressure "
                    f"{zone.get('zone_pressure', 0):.0%}."
                ),
            }
        )
    return sorted(incidents, key=lambda row: row["priority_score"], reverse=True)


def compute_before_after_kpis(repo: BaseRepository, event_id: str) -> dict[str, Any]:
    zones = compute_zone_risk(repo, event_id)
    inventory = compute_inventory_risk(repo, event_id)
    incidents = compute_incident_priority(repo, event_id)
    critical_zones = [zone for zone in zones if zone["status"] == "critical"]
    stockout_risks = [item for item in inventory if item["status"] in {"critical", "warning"}]
    pending_actions = repo.find("actions", {"event_id": event_id, "status": "pending_approval"})
    executed_actions = repo.find("actions", {"event_id": event_id, "status": "executed"})
    riskiest_zone = zones[0] if zones else {}
    highest_stock = inventory[0] if inventory else {}
    projected_pressure_after = max(riskiest_zone.get("zone_pressure", 0) - 0.15 * len(executed_actions), 0.35)
    projected_wait_after = max(riskiest_zone.get("avg_wait_min", 0) - 3 * len(executed_actions), 2)
    return {
        "overall_risk": "critical" if critical_zones or len(stockout_risks) >= 3 else "warning",
        "crowd_risk": round(riskiest_zone.get("zone_pressure", 0), 3),
        "longest_wait_min": max([zone["avg_wait_min"] for zone in zones], default=0),
        "stockout_risks": len(stockout_risks),
        "open_incidents": len([incident for incident in incidents if incident.get("status") == "open"]),
        "pending_actions": len(pending_actions),
        "executed_actions": len(executed_actions),
        "before_after": {
            "before_pressure": round(riskiest_zone.get("zone_pressure", 0), 3),
            "after_pressure": round(projected_pressure_after, 3),
            "before_wait_min": riskiest_zone.get("avg_wait_min", 0),
            "after_wait_min": round(projected_wait_after, 1),
            "before_stockout_risk": round(highest_stock.get("stockout_risk", 0), 3),
            "after_stockout_risk": round(max(highest_stock.get("stockout_risk", 0) - 0.35 * len(executed_actions), 0.35), 3),
        },
    }


def get_current_event_snapshot(repo: BaseRepository, event_id: str = "event_wc_demo_001") -> dict[str, Any]:
    event = repo.find_one("events", {"_id": event_id})
    venue = repo.find_one("venues", {"_id": event.get("venue_id")}) if event else None
    zone_risks = compute_zone_risk(repo, event_id)
    inventory_risks = compute_inventory_risk(repo, event_id)
    incident_priorities = compute_incident_priority(repo, event_id)
    actions = repo.find("actions", {"event_id": event_id})
    agent_runs = repo.aggregate("agent_runs", [{"$match": {"event_id": event_id}}, {"$sort": {"created_at": -1}}, {"$limit": 5}])
    return {
        "event": event,
        "venue": venue,
        "generated_at": repo.find_one("telemetry", {"event_id": event_id}) or {},
        "zone_risks": zone_risks,
        "inventory_risks": inventory_risks,
        "incident_priorities": incident_priorities,
        "actions": sorted(actions, key=lambda row: row.get("created_at", ""), reverse=True),
        "recent_agent_runs": agent_runs,
        "kpis": compute_before_after_kpis(repo, event_id),
    }
