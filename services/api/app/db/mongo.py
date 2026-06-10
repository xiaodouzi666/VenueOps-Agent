from __future__ import annotations

import copy
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from app.config import settings

logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).resolve().parents[4]
SEED_DIR = ROOT_DIR / "data" / "seed"

COLLECTIONS = (
    "venues",
    "zones",
    "events",
    "telemetry",
    "tenants",
    "inventory",
    "staff_shifts",
    "incidents",
    "sop_docs",
    "actions",
    "agent_runs",
    "action_audit",
    "digital_signage",
    "maintenance_tickets",
    "campaign_drafts",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_seed_data() -> dict[str, list[dict[str, Any]]]:
    data: dict[str, list[dict[str, Any]]] = {name: [] for name in COLLECTIONS}
    for path in SEED_DIR.glob("*.json"):
        data[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    for name in COLLECTIONS:
        data.setdefault(name, [])
    return data


def get_nested(document: dict[str, Any], path: str) -> Any:
    current: Any = document
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def match_query(document: dict[str, Any], query: dict[str, Any] | None) -> bool:
    if not query:
        return True
    for key, expected in query.items():
        actual = get_nested(document, key)
        if isinstance(expected, dict):
            for operator, value in expected.items():
                if operator == "$in" and actual not in value:
                    return False
                if operator == "$ne" and actual == value:
                    return False
                if operator == "$gt" and not (actual is not None and actual > value):
                    return False
                if operator == "$gte" and not (actual is not None and actual >= value):
                    return False
                if operator == "$lt" and not (actual is not None and actual < value):
                    return False
                if operator == "$lte" and not (actual is not None and actual <= value):
                    return False
        elif actual != expected:
            return False
    return True


def apply_update(document: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    updated = copy.deepcopy(document)
    set_values = update.get("$set", update)
    for key, value in set_values.items():
        parts = key.split(".")
        target = updated
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    push_values = update.get("$push", {})
    for key, value in push_values.items():
        parts = key.split(".")
        target = updated
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target.setdefault(parts[-1], []).append(value)
    return updated


class BaseRepository:
    backend_name = "base"
    database_name = settings.mongodb_db

    def find(self, collection: str, query: dict[str, Any] | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def find_one(self, collection: str, query: dict[str, Any] | None = None) -> dict[str, Any] | None:
        results = self.find(collection, query=query, limit=1)
        return results[0] if results else None

    def count(self, collection: str, query: dict[str, Any] | None = None) -> int:
        return len(self.find(collection, query=query, limit=None))

    def insert_one(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def update_one(self, collection: str, query: dict[str, Any], update: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError

    def replace_all(self, seed: dict[str, list[dict[str, Any]]]) -> None:
        raise NotImplementedError

    def aggregate(self, collection: str, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Local fallback supports the simple filter/sort/limit stages used by demo traces.
        rows = self.find(collection)
        for stage in pipeline:
            if "$match" in stage:
                rows = [row for row in rows if match_query(row, stage["$match"])]
            elif "$sort" in stage:
                sort_spec = stage["$sort"]
                for key, direction in reversed(list(sort_spec.items())):
                    rows = sorted(rows, key=lambda row: get_nested(row, key) or "", reverse=direction < 0)
            elif "$limit" in stage:
                rows = rows[: int(stage["$limit"])]
        return rows

    def collection_schema(self, collection: str) -> dict[str, Any]:
        sample = self.find(collection, limit=20)
        fields: dict[str, str] = {}
        for doc in sample:
            for key, value in doc.items():
                fields[key] = type(value).__name__
        return {"collection": collection, "fields": fields, "sample_count": len(sample)}


class InMemoryRepository(BaseRepository):
    backend_name = "bundled_demo_store"

    def __init__(self) -> None:
        self._data = load_seed_data()

    def find(self, collection: str, query: dict[str, Any] | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        rows = [copy.deepcopy(row) for row in self._data.get(collection, []) if match_query(row, query)]
        if limit is not None:
            rows = rows[: min(limit, settings.max_query_limit)]
        return rows

    def insert_one(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        self._data.setdefault(collection, []).append(copy.deepcopy(document))
        return copy.deepcopy(document)

    def update_one(self, collection: str, query: dict[str, Any], update: dict[str, Any]) -> dict[str, Any] | None:
        rows = self._data.setdefault(collection, [])
        for index, document in enumerate(rows):
            if match_query(document, query):
                rows[index] = apply_update(document, update)
                return copy.deepcopy(rows[index])
        return None

    def replace_all(self, seed: dict[str, list[dict[str, Any]]]) -> None:
        self._data = copy.deepcopy(seed)


class MongoRepository(BaseRepository):
    backend_name = "mongodb_atlas"

    def __init__(self, uri: str, database_name: str) -> None:
        from pymongo import MongoClient

        self.database_name = database_name
        self.client = MongoClient(uri, serverSelectionTimeoutMS=8000)
        self.db = self.client[database_name]
        self.client.admin.command("ping")

    def find(self, collection: str, query: dict[str, Any] | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        cursor = self.db[collection].find(query or {})
        if limit is not None:
            cursor = cursor.limit(min(limit, settings.max_query_limit))
        return [self._clean(row) for row in cursor]

    def aggregate(self, collection: str, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self._clean(row) for row in self.db[collection].aggregate(pipeline)]

    def count(self, collection: str, query: dict[str, Any] | None = None) -> int:
        return self.db[collection].count_documents(query or {})

    def insert_one(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        self.db[collection].insert_one(copy.deepcopy(document))
        return copy.deepcopy(document)

    def update_one(self, collection: str, query: dict[str, Any], update: dict[str, Any]) -> dict[str, Any] | None:
        self.db[collection].update_one(query, update)
        return self.find_one(collection, query)

    def replace_all(self, seed: dict[str, list[dict[str, Any]]]) -> None:
        for name, rows in seed.items():
            self.db[name].delete_many({})
            if rows:
                self.db[name].insert_many(copy.deepcopy(rows))

    def collection_schema(self, collection: str) -> dict[str, Any]:
        schema = super().collection_schema(collection)
        schema["backend"] = self.backend_name
        return schema

    @staticmethod
    def _clean(document: dict[str, Any]) -> dict[str, Any]:
        cleaned = copy.deepcopy(document)
        if "_id" in cleaned:
            cleaned["_id"] = str(cleaned["_id"])
        return cleaned


_repository: BaseRepository | None = None
_repository_error: str | None = None


def get_repository(force_memory: bool = False) -> BaseRepository:
    global _repository, _repository_error
    if force_memory:
        _repository = InMemoryRepository()
        _repository_error = None
        return _repository
    if _repository is not None:
        return _repository
    if settings.mongodb_uri:
        try:
            _repository = MongoRepository(settings.mongodb_uri, settings.mongodb_db)
            _repository_error = None
            return _repository
        except Exception as exc:
            # The hackathon demo should still run locally without secrets or Atlas access.
            _repository_error = type(exc).__name__
            logger.warning("MongoDB Atlas connection failed; using fallback repository: %s", _repository_error)
            fallback = InMemoryRepository()
            if settings.demo_mode:
                _repository = fallback
            return fallback
    _repository = InMemoryRepository()
    _repository_error = None
    return _repository


def get_repository_error() -> str | None:
    return _repository_error


def reset_repository_to_seed() -> BaseRepository:
    repo = get_repository()
    repo.replace_all(load_seed_data())
    return repo


def next_id(prefix: str, existing: Iterable[dict[str, Any]]) -> str:
    values = []
    for item in existing:
        raw = str(item.get("_id", ""))
        if raw.startswith(f"{prefix}_"):
            try:
                values.append(int(raw.split("_")[-1]))
            except ValueError:
                continue
    return f"{prefix}_{max(values, default=0) + 1:04d}"
