from app.agents.root_agent import run_venueops_agent
from app.db.mongo import get_repository
from app.tools.action_tools import approve_action


MISSION = "Kickoff is in 75 minutes. Keep fans moving, avoid stockouts, and handle facility incidents."


def test_agent_run_creates_mcp_trace_and_pending_actions():
    repo = get_repository(force_memory=True)

    result = run_venueops_agent(repo, MISSION)

    assert result["required_confirmations"] == 5
    assert len(result["recommended_actions"]) >= 5
    assert len(result["tool_trace"]) >= 10
    tools = {step["tool"] for step in result["tool_trace"]}
    assert "mongodb.aggregate" in tools
    assert "mongodb.find" in tools
    assert "mongodb.count" in tools
    assert "mongodb.collection-schema" in tools
    assert "gemini.plan" in tools
    assert "create_pending_action" in tools
    assert result["evidence"]
    assert result["planner"]["mode"] == "deterministic_fallback"
    assert result["planner"]["ranked_actions"]


def test_approving_staff_dispatch_executes_and_audits():
    repo = get_repository(force_memory=True)
    result = run_venueops_agent(repo, MISSION)
    staff_action = next(action for action in result["recommended_actions"] if action["type"] == "staff_dispatch")

    executed = approve_action(repo, staff_action["_id"], "test_operator")

    assert executed["status"] == "executed"
    assert executed["approved_by"] == "test_operator"
    dispatched = repo.find("staff_shifts", {"assigned_zone": "gate_b", "status": "dispatched"})
    assert len(dispatched) == 4
    audit = repo.find("action_audit", {"action_id": staff_action["_id"]})
    assert any(row["event"] == "executed" for row in audit)
