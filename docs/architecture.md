# Architecture

VenueOps Agent is a two-service web app:

- `apps/web`: Next.js command center dashboard.
- `services/api`: FastAPI backend with agent orchestration, business tools, MongoDB access, and demo simulation.

The agent uses a guarded tool-execution pattern: tools are allowlisted, high-impact actions require approval, and every tool call is recorded for auditability.

## Runtime Flow

```text
Operator
  -> Next.js dashboard
  -> FastAPI /api/agent/run
  -> VenueOps Orchestrator
     -> MongoDB MCP Server-backed reads in hosted mode
     -> deterministic risk tools
     -> Atlas Vector Search-first SOP retriever with local fallback ranking
     -> Gemini planner on Vertex AI, with deterministic fallback
     -> pending action writer
  -> actions / agent_runs / audit trail
  -> dashboard verification
```

## Production Integration Points

- Google Cloud Run hosts API and web services.
- Google Secret Manager provides MongoDB and MCP connection strings.
- Gemini on Vertex AI can draft the structured operations strategy and final judge-facing explanation.
- Google ADK wrapper in `services/api/app/agents/adk_agent.py` defines the same tool surface for Agent Builder / Agent Platform alignment.
- MongoDB Atlas stores operational collections and agent memory.
- MongoDB MCP Server provides the database tool surface for agentic reads.

## Local Demo Mode

When secrets are not configured, the backend uses the bundled seed data and records fallback trace entries with the same tool names and guardrails. The hosted demo should use MongoDB Atlas, `VENUEOPS_USE_REAL_MCP=true`, and `transport: mongodb-mcp-server` in the visible Tool Trace.
