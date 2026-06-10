# P0/P1 Completion Audit

Current audit date: 2026-06-10.

This file tracks the concrete evidence for the requested P0 and P1 scope. It separates product/code completion from external submission work that requires account access.

## P0

| Requirement | Current status | Evidence |
| --- | --- | --- |
| Web app accessible with dashboard and agent chat | Locally complete; deployment scripts present | `apps/web/src/components/DashboardClient.tsx`, `apps/web/src/components/VenueMap.tsx`, `apps/web/src/components/ActionQueue.tsx`, runtime API proxy in `apps/web/src/app/api/backend/[...path]/route.ts`, local `http://localhost:3000`, `infra/scripts/deploy.sh` |
| Cloud Run hosted app | Deployment assets complete; actual hosted URL requires gcloud auth, project, and secrets | `services/api/Dockerfile`, `apps/web/Dockerfile`, `infra/cloudbuild-api.yaml`, `infra/scripts/setup_secrets.sh`, `infra/scripts/preflight.sh`, `infra/scripts/deploy.sh`; deploy grants API runtime IAM for Vertex AI and MongoDB secrets; `gcloud` is installed but no active account/project is configured on this machine |
| Gemini / Google Agent Platform participates in core reasoning | Vertex/Gemini hook implemented; deterministic demo fallback runs without secrets; Cloud Run deploy passes project, location, model env vars, and API service account | `services/api/app/agents/root_agent.py` `_optional_gemini_explanation`, `.env.example`, `README.md`, `infra/scripts/deploy.sh`, `infra/cloudrun/api-service.yaml` |
| MongoDB MCP integration | Implemented as MCP stdio path plus deterministic trace fallback | `services/api/app/tools/mongodb_mcp.py`, `docs/mongodb_mcp_setup.md`; traces include `mongodb.find`, `mongodb.aggregate`, `mongodb.count`, `mongodb.collection-schema` |
| MongoDB Atlas stores business data | Atlas-ready repository implemented; local seed fallback included | `services/api/app/db/mongo.py`, `data/seed/*.json`, `services/api/app/db/indexes.py` |
| Multi-step task with at least five tool calls | Complete | Agent run emits schema, aggregate, find, find, count, SOP aggregate, and five action writes |
| Human confirmation for operational actions | Complete | `services/api/app/tools/action_tools.py`, `services/api/app/routes/actions.py`, approval cards in `apps/web/src/components/ActionQueue.tsx` |
| Reproducible demo reset and crowd surge | Complete | `services/api/app/tools/simulation_tools.py`, `services/api/app/routes/demo.py`, `apps/web/src/components/ScenarioControls.tsx` |
| Public open-source repo | Complete | Source pushed to `https://github.com/xiaodouzi666/VenueOps-Agent.git` on `main` |
| License | Complete | `LICENSE` |
| README | Complete except external hosted Cloud Run URL | `README.md` |
| 3-minute English demo video | Complete | `docs/demo_assets/venueops_demo.mp4`, generated from real app screenshots and English narration via `scripts/build_demo_video.py` |

## P1

| Requirement | Current status | Evidence |
| --- | --- | --- |
| MongoDB Search / Vector Search SOP retrieval | Complete for app behavior; Atlas index creation documented | `data/seed/sop_docs.json`, `services/api/app/tools/sop_retriever.py`, `services/api/app/db/indexes.py`, `docs/mongodb_mcp_setup.md` |
| Heatmap / zone risk visualization | Complete | `apps/web/src/components/VenueMap.tsx` |
| Action audit trail | Complete | `services/api/app/tools/action_tools.py`, `action_audit` seed collection, action cards show visible audit events in `apps/web/src/components/ActionQueue.tsx` |
| Before/After KPI | Complete | `services/api/app/tools/risk_tools.py` `compute_before_after_kpis`, `apps/web/src/components/BeforeAfter.tsx` |
| Tool trace panel | Complete | `services/api/app/tools/mongodb_mcp.py`, `apps/web/src/components/ToolTrace.tsx` |

## Verification Commands

Final local verification on 2026-06-10 after the Cloud Run runtime env and IAM fix:

- `services/api/.venv/bin/pytest`: passed, 5 tests.
- `npm --workspace apps/web run build`: passed.
- `bash -n infra/scripts/enable_gcp_services.sh infra/scripts/preflight.sh infra/scripts/setup_secrets.sh infra/scripts/deploy.sh`: passed.
- YAML parse check for `infra/cloudrun/api-service.yaml`, `infra/cloudrun/web-service.yaml`, and `infra/cloudbuild-api.yaml`: passed.
- `infra/scripts/preflight.sh`: gcloud installed; still blocked by missing active account and missing project on this workstation.
- `docker build -f services/api/Dockerfile -t venueops-api:local .`: passed.
- `docker build -t venueops-web:local apps/web`: passed.
- Web proxy smoke: passed through `/api/backend/*`, including health, dashboard snapshot, agent run, approvals, audit, and KPI checks.
- `python3 scripts/build_demo_video.py`: passed; produced 00:03:00 MP4 with 1280x720 video and AAC audio.
- Terminal smoke flow: passed health, reset, crowd surge, agent run, >=5 tool calls, 5 pending approvals, approve/reject actions, audit log, KPI improvement, docs page.
- Built-in browser flow: passed dashboard load, reset, crowd surge, agent run, approve/reject actions, visible action audit trail, tool trace, SOP evidence, before/after KPI, docs page, with zero console errors during the test window.

```bash
cd services/api
.venv/bin/pytest

cd ../../apps/web
npm run build

cd ../..
docker build -f services/api/Dockerfile -t venueops-api:local .
docker build -t venueops-web:local apps/web
```

## External Completion Needed

These items cannot be proven complete from this workstation unless the required credentials are present:

1. Authenticate `gcloud`, export `GOOGLE_CLOUD_PROJECT`, optionally export `GOOGLE_CLOUD_REGION`, `GOOGLE_CLOUD_LOCATION`, and `GEMINI_MODEL`, then set the project with `gcloud config set project <project-id>`.
2. Run `infra/scripts/enable_gcp_services.sh`.
3. Export `MONGODB_URI` and `MDB_MCP_CONNECTION_STRING`, then run `infra/scripts/setup_secrets.sh`.
4. Run `infra/scripts/preflight.sh` to verify account, project, APIs, and required secrets.
5. Run `infra/scripts/deploy.sh`.
6. Replace the README hosted Cloud Run URL once it exists.
