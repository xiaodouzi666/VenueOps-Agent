# VenueOps Agent

AI operations copilot for retail and event venues, built for the Google Cloud Rapid Agent Hackathon MongoDB track.

VenueOps Agent helps stadiums, malls, fan zones, airports, and event venues handle peak-time operations: crowd congestion, queue overflow, stockouts, staff dispatch, facility incidents, and tenant campaigns.

It uses Gemini on Google Cloud Agent Platform as the intended planning layer, MongoDB Atlas as operational memory, MongoDB Aggregation for risk analytics, MongoDB Search / Vector Search for SOP retrieval, and the MongoDB MCP Server as the agentic data access layer. The local demo runs deterministically without secrets, then switches to real MongoDB / Vertex AI when environment variables are configured.

## Live Demo

Cloud Run URL: pending deployment.

Deployment preflight:

```bash
gcloud auth login
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_REGION=us-central1
export GOOGLE_CLOUD_LOCATION=us-central1
export GEMINI_MODEL=gemini-3-pro
gcloud config set project "$GOOGLE_CLOUD_PROJECT"

infra/scripts/enable_gcp_services.sh

export MONGODB_URI="mongodb+srv://..."
export MDB_MCP_CONNECTION_STRING="mongodb+srv://..."
infra/scripts/setup_secrets.sh

infra/scripts/preflight.sh
infra/scripts/deploy.sh
```

`deploy.sh` also grants the API Cloud Run service account access to Vertex AI and the MongoDB Secret Manager secrets. Set `CLOUD_RUN_SERVICE_ACCOUNT` before running it if you do not want to use the project compute default service account.

## Demo Video

3-minute demo video: [docs/demo_assets/venueops_demo.mp4](docs/demo_assets/venueops_demo.mp4)

Public GitHub video URL:
`https://github.com/xiaodouzi666/VenueOps-Agent/blob/main/docs/demo_assets/venueops_demo.mp4`

## Built With

- Gemini / Google Cloud Agent Platform
- Google ADK-compatible tool orchestration patterns
- Google Cloud Run
- Google Secret Manager
- MongoDB Atlas
- MongoDB MCP Server
- MongoDB Aggregation
- MongoDB Search / Vector Search
- Next.js
- FastAPI

## What It Does

Demo mission:

```text
Kickoff is in 75 minutes. Keep fans moving, avoid stockouts, and handle facility incidents.
```

The agent performs an observe-analyze-retrieve-plan-confirm-act-verify loop:

1. Reads current event data through MongoDB MCP-style tools.
2. Aggregates crowd, inventory, staffing, and incident risk.
3. Retrieves relevant SOPs from searchable SOP documents.
4. Uses Gemini on Vertex AI as the planner when Google Cloud configuration is present, with deterministic fallback for local judging.
5. Creates a multi-step safe action plan.
6. Stores actions as `pending_approval`.
7. Lets an operator approve or reject each action.
8. Writes status, execution effects, and audit trail back to MongoDB.

## How MongoDB Is Used

1. Operational data store: venues, events, zones, telemetry, tenants, inventory, staff shifts, incidents, actions, SOPs, agent runs.
2. Agent memory: `agent_runs` stores goals, tool traces, plans, and action outcomes.
3. Analytics engine: aggregation-style risk computation for zones, queues, inventory, staffing, and incidents.
4. SOP retrieval: MongoDB Search / Vector Search-ready `sop_docs` with embeddings.
5. MCP tool layer: agent traces show `mongodb.find`, `mongodb.aggregate`, `mongodb.count`, and `mongodb.collection-schema` calls.

## Run Locally

Backend:

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn main:app --reload --port 8080
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment

Copy `.env.example` into `services/api/.env` and configure real integrations when available. Without secrets, the demo uses the bundled deterministic seed data.

```bash
MONGODB_URI=mongodb+srv://...
MONGODB_DB=venueops_demo
MDB_MCP_CONNECTION_STRING=mongodb+srv://...
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
GEMINI_MODEL=gemini-3-pro
BACKEND_API_BASE_URL=http://localhost:8080
```

The web app calls a same-origin Next.js proxy at `/api/backend/*`; Cloud Run sets `BACKEND_API_BASE_URL` at runtime so the browser never needs a baked-in API URL.

## Security And Guardrails

- Demo data is synthetic and contains no PII.
- Production MCP mode should use a read-only MongoDB user.
- Write operations are not arbitrary database writes. They go through allowlisted business tools.
- High-impact actions stay pending until a human approves them.
- Destructive operations such as drop, delete, and arbitrary updates are blocked by policy.
- Every action stores rationale, data evidence, risk level, approver, and audit events.

## Judging Alignment

- Technological implementation: Gemini/Google Cloud-ready planner orchestration, MongoDB MCP trace, MongoDB Aggregation, Search/Vector Search-ready SOP retrieval, Cloud Run deployment assets.
- Design: command-center UI with heatmap, KPIs, action queue, tool trace, and evidence.
- Potential impact: applies to World Cup fan zones, stadiums, malls, airports, and event venues.
- Quality of idea: agentic operations workflow, not a chat-only dashboard.
