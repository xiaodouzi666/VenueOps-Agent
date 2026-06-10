from fastapi import APIRouter

from app.db.mongo import get_repository

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "venueops-agent-api"}


@router.get("/readyz")
def readyz() -> dict:
    repo = get_repository()
    return {"status": "ready", "backend": repo.backend_name, "database": repo.database_name}
