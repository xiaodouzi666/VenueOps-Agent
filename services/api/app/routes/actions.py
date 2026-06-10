from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.db.mongo import get_repository
from app.tools.action_tools import approve_action, reject_action

router = APIRouter()


class ApproveRequest(BaseModel):
    approver: str = "demo_operator"


class RejectRequest(BaseModel):
    reason: str = "Operator rejected during demo."
    actor: str = "demo_operator"


@router.get("")
def list_actions(event_id: str = "event_wc_demo_001") -> dict:
    repo = get_repository()
    actions = repo.aggregate("actions", [{"$match": {"event_id": event_id}}, {"$sort": {"created_at": -1}}])
    audit = repo.find("action_audit", limit=100)
    return {"actions": actions, "audit": audit}


@router.post("/{action_id}/approve")
def approve(action_id: str, request: ApproveRequest) -> dict:
    repo = get_repository()
    try:
        action = approve_action(repo, action_id, request.approver)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"action": action}


@router.post("/{action_id}/reject")
def reject(action_id: str, request: RejectRequest) -> dict:
    repo = get_repository()
    try:
        action = reject_action(repo, action_id, request.reason, request.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"action": action}
