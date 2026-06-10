# MongoDB MCP Setup

Production should run MongoDB MCP in read-only mode for exploration and aggregation. Mutating operations should stay behind the VenueOps action API.

Recommended environment:

```bash
MDB_MCP_CONNECTION_STRING="mongodb+srv://readonly-user:..."
MDB_MCP_READ_ONLY=true
VENUEOPS_USE_REAL_MCP=true
```

The app records these MCP calls in `agent_runs.steps`:

- `mongodb.collection-schema`
- `mongodb.aggregate`
- `mongodb.find`
- `mongodb.count`

In local demo mode, the bridge executes against seed data but keeps the same tool names, trace schema, and policy checks. When `VENUEOPS_USE_REAL_MCP=true` and `MDB_MCP_CONNECTION_STRING` is present, the backend attempts `npx -y mongodb-mcp-server@latest` stdio `tools/call` requests for `find`, `aggregate`, `count`, and `collection-schema`; if the MCP server is unavailable, the response trace is marked `fallback` and the deterministic repository path keeps the demo running.
