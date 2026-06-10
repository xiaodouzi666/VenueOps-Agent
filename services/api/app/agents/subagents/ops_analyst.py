from __future__ import annotations

from typing import Any

from app.db.mongo import BaseRepository
from app.tools.risk_tools import compute_zone_risk


def analyze_ops(repo: BaseRepository, event_id: str) -> dict[str, Any]:
    zone_risks = compute_zone_risk(repo, event_id)
    return {
        "top_zone_risks": zone_risks[:4],
        "critical_zones": [zone for zone in zone_risks if zone["status"] == "critical"],
        "source_collections": ["telemetry", "zones", "staff_shifts"],
    }
