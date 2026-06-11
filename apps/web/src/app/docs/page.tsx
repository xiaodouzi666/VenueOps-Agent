import Link from "next/link";

export default function DocsPage() {
  return (
    <main className="docPage">
      <Link className="button" href="/">Back to dashboard</Link>
      <h1>VenueOps Agent Architecture</h1>
      <p>
        VenueOps Agent is an operations copilot for stadium, fan-zone, and retail venue teams.
        It combines MongoDB operational data, MongoDB MCP Server-backed reads, SOP retrieval,
        risk formulas, Gemini planning, a Google ADK agent definition, human approval, and
        auditable agent memory.
      </p>

      <h2>Agent Loop</h2>
      <ol>
        <li>Observe: query events, telemetry, inventory, staff, incidents, actions, and SOPs.</li>
        <li>Analyze: compute zone pressure, queue risk, stockout risk, staffing gap, and incident priority.</li>
        <li>Retrieve: attempt Atlas Vector Search-first SOP retrieval, then use deterministic fallback ranking when offline.</li>
        <li>Plan: create five concrete operational actions with evidence and expected impact.</li>
        <li>Confirm: keep high-impact actions in pending approval.</li>
        <li>Act: execute approved actions through allowlisted business tools.</li>
        <li>Verify: write state changes and audit logs back to MongoDB.</li>
      </ol>

      <h2>Google ADK / Agent Builder</h2>
      <p>
        The repository includes a Google ADK agent wrapper in `services/api/app/agents/adk_agent.py`.
        Hosted planning uses Gemini on Vertex AI through the configured `GEMINI_MODEL`, with
        `gemini.plan` recorded in the Tool Trace.
      </p>

      <h2>MongoDB Collections</h2>
      <p>
        `venues`, `events`, `zones`, `telemetry`, `tenants`, `inventory`, `staff_shifts`,
        `incidents`, `actions`, `action_audit`, `sop_docs`, and `agent_runs`.
      </p>

      <h2>Guardrails</h2>
      <p>
        The hosted agent can read operational data through MongoDB MCP Server-backed tools. Mutating behavior is
        restricted to business tools that create pending actions, approve or reject them, and write
        bounded simulated effects. Destructive database operations are blocked, and the visible trace
        shows whether reads used `mongodb-mcp-server` transport or the deterministic local bridge.
      </p>
    </main>
  );
}
