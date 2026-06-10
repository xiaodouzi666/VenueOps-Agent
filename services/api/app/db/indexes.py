from __future__ import annotations

from app.db.mongo import MongoRepository


INDEXES = {
    "telemetry": [
        [("event_id", 1), ("zone_id", 1), ("timestamp", -1)],
        [("event_id", 1), ("timestamp", -1)],
    ],
    "inventory": [
        [("event_id", 1), ("tenant_id", 1), ("sku", 1)],
        [("event_id", 1), ("projected_next_90min", -1)],
    ],
    "staff_shifts": [[("event_id", 1), ("role", 1), ("status", 1), ("assigned_zone", 1)]],
    "incidents": [
        [("event_id", 1), ("status", 1), ("severity", 1)],
        [("event_id", 1), ("zone_id", 1)],
    ],
    "actions": [[("event_id", 1), ("status", 1), ("created_at", -1)]],
    "agent_runs": [[("event_id", 1), ("created_at", -1)]],
}


def ensure_indexes(repo: MongoRepository) -> list[str]:
    created: list[str] = []
    for collection, specs in INDEXES.items():
        for spec in specs:
            created.append(repo.db[collection].create_index(spec))
    return created


VECTOR_SEARCH_INDEX = {
    "name": "sop_vector_index",
    "collection": "sop_docs",
    "definition": {
        "fields": [
            {"type": "vector", "path": "embedding", "numDimensions": 32, "similarity": "cosine"},
            {"type": "filter", "path": "tags"},
        ]
    },
}

TEXT_SEARCH_INDEX = {
    "name": "sop_text_index",
    "collection": "sop_docs",
    "fields": ["title", "content", "tags"],
}
