from __future__ import annotations

from typing import Any

from app.db.mongo import BaseRepository, reset_repository_to_seed, utc_now_iso


def reset_demo_data() -> dict[str, Any]:
    repo = reset_repository_to_seed()
    return {"status": "reset", "backend": repo.backend_name, "database": repo.database_name}


def simulate_event_tick(repo: BaseRepository, event_id: str, scenario: str) -> dict[str, Any]:
    if scenario == "crowd_surge_gate_b":
        repo.insert_one(
            "telemetry",
            {
                "_id": f"tel_gate_b_surge_{utc_now_iso().replace(':', '').replace('-', '')}",
                "event_id": event_id,
                "zone_id": "gate_b",
                "timestamp": utc_now_iso(),
                "people_count": 2165,
                "queue_length": 510,
                "avg_wait_min": 22,
                "dwell_time_min": 11,
                "sensor_confidence": 0.9,
            },
        )
        return {"status": "ok", "scenario": scenario, "changed": ["telemetry.gate_b"]}
    if scenario == "food_stockout":
        for item in repo.find("inventory", {"event_id": event_id}):
            if item.get("sku") in {"water_500ml", "rain_poncho"}:
                repo.update_one(
                    "inventory",
                    {"_id": item["_id"]},
                    {
                        "$set": {
                            "current_stock": max(item.get("current_stock", 0) - 60, 20),
                            "projected_next_90min": item.get("projected_next_90min", 0) + 80,
                            "last_updated": utc_now_iso(),
                        }
                    },
                )
        return {"status": "ok", "scenario": scenario, "changed": ["inventory.water", "inventory.rain_poncho"]}
    if scenario == "facility_incident":
        repo.insert_one(
            "incidents",
            {
                "_id": f"incident_{utc_now_iso().replace(':', '').replace('-', '')}",
                "event_id": event_id,
                "zone_id": "food_court_1",
                "type": "facility",
                "severity": "medium",
                "description": "Spill reported near Food Court 1 queue lane.",
                "status": "open",
                "reported_at": utc_now_iso(),
            },
        )
        return {"status": "ok", "scenario": scenario, "changed": ["incidents.food_court_1"]}
    if scenario == "after_actions":
        repo.insert_one(
            "telemetry",
            {
                "_id": f"tel_gate_b_after_{utc_now_iso().replace(':', '').replace('-', '')}",
                "event_id": event_id,
                "zone_id": "gate_b",
                "timestamp": utc_now_iso(),
                "people_count": 1735,
                "queue_length": 230,
                "avg_wait_min": 11,
                "dwell_time_min": 7,
                "sensor_confidence": 0.9,
            },
        )
        return {"status": "ok", "scenario": scenario, "changed": ["telemetry.gate_b_after_actions"]}
    raise ValueError(f"Unknown scenario: {scenario}")
