import Link from "next/link";

export default function DocsPage() {
  return (
    <main className="docPage">
      <Link className="button" href="/">Back to dashboard</Link>
      <h1>VenueOps Agent Architecture</h1>
      <p>
        VenueOps Agent is an operations copilot for stadium, fan-zone, and retail venue teams.
        It combines MongoDB operational data, SOP retrieval, risk formulas, human approval, and
        auditable agent memory.
      </p>

      <h2>Agent Loop</h2>
      <ol>
        <li>Observe: query events, telemetry, inventory, staff, incidents, actions, and SOPs.</li>
        <li>Analyze: compute zone pressure, queue risk, stockout risk, staffing gap, and incident priority.</li>
        <li>Retrieve: rank SOP documents through Search / Vector Search-ready data.</li>
        <li>Plan: create five concrete operational actions with evidence and expected impact.</li>
        <li>Confirm: keep high-impact actions in pending approval.</li>
        <li>Act: execute approved actions through allowlisted business tools.</li>
        <li>Verify: write state changes and audit logs back to MongoDB.</li>
      </ol>

      <h2>MongoDB Collections</h2>
      <p>
        `venues`, `events`, `zones`, `telemetry`, `tenants`, `inventory`, `staff_shifts`,
        `incidents`, `actions`, `action_audit`, `sop_docs`, and `agent_runs`.
      </p>

      <h2>Guardrails</h2>
      <p>
        The agent can read operational data through MongoDB MCP-shaped tools. Mutating behavior is
        restricted to business tools that create pending actions, approve or reject them, and write
        bounded simulated effects. Destructive database operations are blocked.
      </p>
    </main>
  );
}
