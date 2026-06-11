from __future__ import annotations

import math
import re
from typing import Any

from app.config import settings
from app.db.mongo import BaseRepository
from app.tools.mongodb_mcp import MongoMCPBridge


def tokenize(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9_]+", text.lower()) if len(token) >= 3}


def hashed_embedding(text: str, dimensions: int = 32) -> list[float]:
    tokens = tokenize(text)
    vector = [0.0 for _ in range(dimensions)]
    for token in tokens:
        index = sum(ord(char) for char in token) % dimensions
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    size = min(len(a), len(b))
    numerator = sum(a[index] * b[index] for index in range(size))
    norm_a = math.sqrt(sum(value * value for value in a[:size])) or 1.0
    norm_b = math.sqrt(sum(value * value for value in b[:size])) or 1.0
    return numerator / (norm_a * norm_b)


def retrieve_relevant_sops(
    repo: BaseRepository,
    mcp: MongoMCPBridge,
    query: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    query_vector = hashed_embedding(query)
    if settings.use_real_mcp and repo.backend_name == "mongodb_atlas":
        vector_docs = mcp.aggregate(
            "sop_docs",
            [
                {
                    "$vectorSearch": {
                        "index": "sop_vector_index",
                        "path": "embedding",
                        "queryVector": query_vector,
                        "numCandidates": 25,
                        "limit": top_k,
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "title": 1,
                        "doc_type": 1,
                        "tags": 1,
                        "content": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ],
            purpose="Run MongoDB Atlas Vector Search over SOP documents",
        )
        if vector_docs:
            return [
                {
                    "_id": doc.get("_id"),
                    "title": doc.get("title"),
                    "doc_type": doc.get("doc_type"),
                    "tags": doc.get("tags", []),
                    "content": doc.get("content"),
                    "score": round(float(doc.get("score") or 0.0), 3),
                    "retrieval_mode": "mongodb_atlas_vector_search",
                }
                for doc in vector_docs[:top_k]
            ]

    docs = mcp.aggregate(
        "sop_docs",
        [{"$match": {}}, {"$limit": 25}],
        purpose="Fallback-rank SOP documents for operational policy evidence when Atlas Vector Search is unavailable",
    )
    query_terms = tokenize(query)
    ranked: list[dict[str, Any]] = []
    for doc in docs:
        text = f"{doc.get('title', '')} {doc.get('content', '')} {' '.join(doc.get('tags', []))}"
        terms = tokenize(text)
        text_score = len(query_terms & terms) / max(len(query_terms), 1)
        vector_score = cosine_similarity(query_vector, doc.get("embedding", []))
        score = 0.55 * text_score + 0.45 * vector_score
        ranked.append(
            {
                "_id": doc.get("_id"),
                "title": doc.get("title"),
                "doc_type": doc.get("doc_type"),
                "tags": doc.get("tags", []),
                "content": doc.get("content"),
                "score": round(score, 3),
                "retrieval_mode": "mongodb_search_vector_ready_local_ranker",
            }
        )
    return sorted(ranked, key=lambda row: row["score"], reverse=True)[:top_k]
