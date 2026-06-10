from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.db.mongo import get_repository
from app.tools.sop_retriever import hashed_embedding


def main() -> None:
    repo = get_repository()
    for doc in repo.find("sop_docs"):
        text = f"{doc.get('title', '')} {doc.get('content', '')} {' '.join(doc.get('tags', []))}"
        repo.update_one("sop_docs", {"_id": doc["_id"]}, {"$set": {"embedding": hashed_embedding(text)}})
    print({"status": "embeddings_updated", "backend": repo.backend_name})


if __name__ == "__main__":
    main()
