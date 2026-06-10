from fastapi import APIRouter

from app.config import settings
from app.db.mongo import get_repository, get_repository_error

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "venueops-agent-api"}


@router.get("/healthz")
def healthz() -> dict:
    return health()


@router.get("/readyz")
def readyz() -> dict:
    repo = get_repository()
    status = "ready"
    if settings.mongodb_uri and not settings.demo_mode and repo.backend_name != "mongodb_atlas":
        status = "degraded"
    payload = {"status": status, "backend": repo.backend_name, "database": repo.database_name}
    if status != "ready":
        payload["error_type"] = get_repository_error()
    return payload
