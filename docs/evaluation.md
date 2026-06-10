# Evaluation

Local gate:

```bash
cd services/api
pytest
cd ../../apps/web
npm run build
```

Runtime smoke, with API on `127.0.0.1:8080` and web on `127.0.0.1:3000`:

```bash
python3 scripts/smoke_api_flow.py
```

Golden mission:

```text
Kickoff is in 75 minutes. Keep fans moving, avoid stockouts, and handle facility incidents.
```

Expected outcome:

- Gate B is the top crowd risk.
- At least one food court SKU is critical.
- An open facility or crowd incident is present.
- Agent trace contains at least five MongoDB MCP-shaped tool steps.
- Agent trace contains `gemini.plan`.
- Five actions are created with `pending_approval`.
- Approving staff dispatch changes staff assignments and writes audit events.
