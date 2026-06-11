# VenueOps Agent

AI operations copilot for retail and event venues, built for the Google Cloud Rapid Agent Hackathon MongoDB track.

VenueOps Agent helps stadiums, malls, fan zones, airports, and event venues handle peak-time operations: crowd congestion, queue overflow, stockouts, staff dispatch, facility incidents, and tenant campaigns.

The hosted demo runs on Cloud Run with MongoDB Atlas, MongoDB MCP Server, and Gemini on Vertex AI as the planning layer. The repository also includes a Google ADK agent definition for Google Cloud Agent Builder / Agent Platform alignment. A deterministic local fallback is included only so judges can reproduce the project without secrets.

## Live Demo

Cloud Run URL: [https://venueops-web-iub7vvtltq-uc.a.run.app](https://venueops-web-iub7vvtltq-uc.a.run.app)

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

The deployment reads `GEMINI_MODEL` from the environment. For the hackathon submission, set it to a Gemini 3 model such as `gemini-3-pro` when that model is enabled in your Google Cloud project and region.

## Demo Video

Public YouTube/Vimeo demo: replace this line with the public Devpost video URL after upload.

Backup MP4 in this repository: [docs/demo_assets/venueops_demo.mp4](docs/demo_assets/venueops_demo.mp4)

The backup MP4 is 3 minutes and English-language, but the final hackathon video field should use a public YouTube or Vimeo URL.

## Built With

- Gemini on Vertex AI / Google Cloud Agent Platform
- Google ADK agent wrapper in `services/api/app/agents/adk_agent.py`
- Google Cloud Run
- Google Secret Manager
- MongoDB Atlas
- MongoDB MCP Server
- MongoDB Aggregation
- MongoDB Atlas Vector Search with local fallback ranking
- Next.js
- FastAPI

## What It Does

Demo mission:

```text
Kickoff is in 75 minutes. Keep fans moving, avoid stockouts, and handle facility incidents.
```

The agent performs an observe-analyze-retrieve-plan-confirm-act-verify loop:

1. Reads current event data through MongoDB MCP Server-backed tools in hosted mode.
2. Aggregates crowd, inventory, staffing, and incident risk.
3. Retrieves relevant SOPs from searchable SOP documents.
4. Uses Gemini on Vertex AI as the planner when Google Cloud configuration is present, with deterministic fallback only for offline local judging.
5. Creates a multi-step safe action plan.
6. Stores actions as `pending_approval`.
7. Lets an operator approve or reject each action.
8. Writes status, execution effects, and audit trail back to MongoDB.

## How MongoDB Is Used

1. Operational data store: venues, events, zones, telemetry, tenants, inventory, staff shifts, incidents, actions, SOPs, agent runs.
2. Agent memory: `agent_runs` stores goals, tool traces, plans, and action outcomes.
3. Analytics engine: aggregation-style risk computation for zones, queues, inventory, staffing, and incidents.
4. SOP retrieval: Atlas Vector Search over `sop_docs` is attempted first in hosted Atlas mode; local fallback ranking keeps offline judging deterministic.
5. MCP tool layer: agent traces show `mongodb.find`, `mongodb.aggregate`, `mongodb.count`, and `mongodb.collection-schema` calls, including the transport (`mongodb-mcp-server` or fallback bridge).

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

Useful routes:

- `/`
- `/dashboard/event_wc_demo_001`
- `/agent`
- `/actions`
- `/docs`

With both services running, execute the reproducible terminal smoke:

```bash
python3 scripts/smoke_api_flow.py
```

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

## Google ADK / Agent Builder Integration

- ADK agent definition: `services/api/app/agents/adk_agent.py`.
- Production planner: Gemini on Vertex AI through `google-genai`.
- Cloud runtime: Cloud Run API and web services.
- Database tools: MongoDB MCP Server launched by the API runtime for read-only database exploration, with guarded business APIs for writes.

## Security And Guardrails

- Demo data is synthetic and contains no PII.
- Production MCP mode should use a read-only MongoDB user.
- Write operations are not arbitrary database writes. They go through allowlisted business tools.
- High-impact actions stay pending until a human approves them.
- Destructive operations such as drop, delete, and arbitrary updates are blocked by policy.
- Every action stores rationale, data evidence, risk level, approver, and audit events.
- The hosted demo uses a synthetic sandbox Atlas database. Reset and simulation endpoints are intentionally public for judging and should be disabled or protected in production.

## Judging Alignment

- Technological implementation: Google ADK agent definition, Gemini/Vertex AI planner orchestration, MongoDB MCP Server trace with visible transport, MongoDB Aggregation, Atlas Vector Search-first SOP retrieval, Cloud Run deployment assets.
- Design: command-center UI with heatmap, KPIs, action queue, tool trace, and evidence.
- Potential impact: applies to World Cup fan zones, stadiums, malls, airports, and event venues.
- Quality of idea: agentic operations workflow, not a chat-only dashboard.
