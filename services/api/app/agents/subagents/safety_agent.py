from __future__ import annotations

from typing import Any

from app.db.mongo import BaseRepository
from app.tools.risk_tools import compute_incident_priority


def analyze_safety(repo: BaseRepository, event_id: str) -> dict[str, Any]:
    incidents = compute_incident_priority(repo, event_id)
    return {
        "top_incidents": incidents[:4],
        "open_incidents": [incident for incident in incidents if incident.get("status") == "open"],
        "source_collections": ["incidents", "telemetry", "zones"],
    }
