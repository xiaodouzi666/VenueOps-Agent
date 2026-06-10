from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.db.mongo import get_repository
from app.tools.simulation_tools import reset_demo_data, simulate_event_tick

router = APIRouter()


class SimulateRequest(BaseModel):
    scenario: str
    event_id: str = "event_wc_demo_001"


@router.post("/reset")
def reset() -> dict:
    return reset_demo_data()


@router.post("/simulate")
def simulate(request: SimulateRequest) -> dict:
    repo = get_repository()
    try:
        return simulate_event_tick(repo, request.event_id, request.scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
