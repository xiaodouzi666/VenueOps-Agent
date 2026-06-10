from __future__ import annotations

import math
import re
from typing import Any

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
    docs = mcp.aggregate(
        "sop_docs",
        [{"$match": {}}, {"$limit": 25}],
        purpose="Search / Vector Search SOP documents for operational policy evidence",
    )
    query_terms = tokenize(query)
    query_vector = hashed_embedding(query)
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
