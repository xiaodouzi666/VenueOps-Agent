from __future__ import annotations

from typing import Any

from app.db.mongo import BaseRepository
from app.tools.risk_tools import compute_inventory_risk


def analyze_retail(repo: BaseRepository, event_id: str) -> dict[str, Any]:
    inventory = compute_inventory_risk(repo, event_id)
    return {
        "top_inventory_risks": inventory[:4],
        "stockout_candidates": [item for item in inventory if item["status"] in {"critical", "warning"}],
        "source_collections": ["inventory", "tenants"],
    }
