from app.agents.adk_agent import venueops_agent
from app.config import settings
from app.tools.sop_retriever import retrieve_relevant_sops


def test_google_adk_agent_definition_exposes_operational_tools():
    tool_names = {tool.name for tool in venueops_agent.tools}

    assert venueops_agent.name == "venueops_agent"
    assert venueops_agent.model == settings.gemini_model
    assert {
        "get_current_event_snapshot_tool",
        "compute_zone_risk_tool",
        "compute_inventory_risk_tool",
        "compute_incident_priority_tool",
        "create_pending_action_tool",
    }.issubset(tool_names)


def test_sop_retriever_uses_atlas_vector_search_first(monkeypatch):
    class FakeAtlasRepo:
        backend_name = "mongodb_atlas"

    class FakeMcp:
        def __init__(self):
            self.calls = []

        def aggregate(self, collection, pipeline, purpose):
            self.calls.append({"collection": collection, "pipeline": pipeline, "purpose": purpose})
            return [
                {
                    "_id": "sop_001",
                    "title": "Gate Overflow Procedure",
                    "doc_type": "sop",
                    "tags": ["gate", "crowd"],
                    "content": "Open overflow lanes when gate pressure exceeds threshold.",
                    "score": 0.91,
                }
            ]

    monkeypatch.setattr(settings, "use_real_mcp", True)
    fake_mcp = FakeMcp()

    docs = retrieve_relevant_sops(FakeAtlasRepo(), fake_mcp, "gate crowd overflow", top_k=1)

    assert fake_mcp.calls[0]["pipeline"][0]["$vectorSearch"]["index"] == "sop_vector_index"
    assert fake_mcp.calls[0]["purpose"] == "Run MongoDB Atlas Vector Search over SOP documents"
    assert docs[0]["retrieval_mode"] == "mongodb_atlas_vector_search"
