# MongoDB MCP Setup

Production should run MongoDB MCP in read-only mode for exploration and aggregation. Mutating operations should stay behind the VenueOps action API.

Recommended environment:

```bash
MDB_MCP_CONNECTION_STRING="mongodb+srv://readonly-user:..."
MDB_MCP_READ_ONLY=true
VENUEOPS_USE_REAL_MCP=true
```

The app records these MCP calls in `agent_runs.steps`, including the visible `transport` field used by the frontend Tool Trace:

- `mongodb.collection-schema`
- `mongodb.aggregate`
- `mongodb.find`
- `mongodb.count`

In hosted mode, set `VENUEOPS_USE_REAL_MCP=true` and `MDB_MCP_CONNECTION_STRING` so the backend launches the official MongoDB MCP Server over stdio for `find`, `aggregate`, `count`, and `collection-schema`. The Cloud Run API image preinstalls `mongodb-mcp-server`; local runs fall back to `npx -y mongodb-mcp-server@latest` when the binary is not already available. Successful hosted calls display `transport: mongodb-mcp-server` in the UI.

In local demo mode, the bridge executes against seed data but keeps the same tool names, trace schema, and policy checks. If the MCP server or Atlas Vector Search index is unavailable, the response trace is marked `fallback` and the deterministic repository path keeps the demo running.
