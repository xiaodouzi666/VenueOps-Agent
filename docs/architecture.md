# Architecture

VenueOps Agent is a two-service web app:

- `apps/web`: Next.js command center dashboard.
- `services/api`: FastAPI backend with agent orchestration, business tools, MongoDB access, and demo simulation.

The agent follows the same pattern used by robust local agents: construct candidate tools first, filter or guard them with policy, execute through a thin runtime, and record every tool result. This mirrors the useful patterns in the local Hermes and OpenClaw codebases without copying their full runtime.

## Runtime Flow

```text
Operator
  -> Next.js dashboard
  -> FastAPI /api/agent/run
  -> VenueOps Orchestrator
     -> MongoDB MCP-shaped reads
     -> deterministic risk tools
     -> SOP Search / Vector Search retriever
     -> pending action writer
  -> actions / agent_runs / audit trail
  -> dashboard verification
```

## Production Integration Points

- Google Cloud Run hosts API and web services.
- Google Secret Manager provides MongoDB and MCP connection strings.
- Gemini on Vertex AI can generate the final judge-facing explanation.
- MongoDB Atlas stores operational collections and agent memory.
- MongoDB MCP Server provides the database tool surface for agentic reads.

## Local Demo Mode

When secrets are not configured, the backend uses the bundled seed data and records MCP-shaped trace entries. This keeps the demo deterministic while preserving the same tool names and guardrails used by the real MCP path.
