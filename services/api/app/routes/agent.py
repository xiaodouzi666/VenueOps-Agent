from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.agents.root_agent import run_venueops_agent
from app.db.mongo import get_repository

router = APIRouter()


class AgentRunRequest(BaseModel):
    mission: str = Field(
        default="Kickoff is in 75 minutes. Keep fans moving, avoid stockouts, and handle facility incidents.",
        min_length=5,
    )
    event_id: str = "event_wc_demo_001"


@router.post("/run")
def run_agent(request: AgentRunRequest) -> dict:
    repo = get_repository()
    return run_venueops_agent(repo, request.mission, request.event_id)


@router.get("/runs")
def list_agent_runs(event_id: str = "event_wc_demo_001") -> dict:
    repo = get_repository()
    runs = repo.aggregate("agent_runs", [{"$match": {"event_id": event_id}}, {"$sort": {"created_at": -1}}, {"$limit": 10}])
    return {"runs": runs}
