from fastapi import APIRouter, Query

from app.db.mongo import get_repository
from app.tools.risk_tools import get_current_event_snapshot

router = APIRouter()


@router.get("/snapshot")
def snapshot(event_id: str = Query(default="event_wc_demo_001")) -> dict:
    repo = get_repository()
    return get_current_event_snapshot(repo, event_id)
