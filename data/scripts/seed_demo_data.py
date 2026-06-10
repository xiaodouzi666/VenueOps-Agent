from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.db.mongo import get_repository, load_seed_data
from app.db.indexes import ensure_indexes


def main() -> None:
    repo = get_repository()
    repo.replace_all(load_seed_data())
    if repo.backend_name == "mongodb_atlas":
        ensure_indexes(repo)  # type: ignore[arg-type]
    print({"status": "seeded", "backend": repo.backend_name, "database": repo.database_name})


if __name__ == "__main__":
    main()
