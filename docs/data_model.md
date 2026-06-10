# Data Model

Database name: `venueops_demo`.

Core collections:

- `venues`: venue metadata and capacity.
- `zones`: zone thresholds, neighbors, staffing defaults, and map rectangles.
- `events`: current event and risk profile.
- `telemetry`: people count, queue length, wait time, dwell time, sensor confidence.
- `tenants`: retail and food tenant metadata.
- `inventory`: SKU stock and projected demand.
- `staff_shifts`: staff roles, skills, assignment, and status.
- `incidents`: facility and crowd incidents.
- `sop_docs`: searchable SOP content with embeddings.
- `actions`: pending, approved, executed, rejected operational actions.
- `action_audit`: action state-change log.
- `agent_runs`: user goals, tool traces, plan summaries, and recommended actions.

Recommended indexes are implemented in `services/api/app/db/indexes.py`. SOP documents are prepared for a text search index and a 32-dimensional vector index.
