# Security

VenueOps Agent is designed around least privilege and human approval.

## Data Safety

- The bundled demo data is synthetic.
- No PII is required for the demo scenario.
- Secrets are read from environment variables or Secret Manager and never committed.

## Tool Guardrails

- Read collections are allowlisted.
- Write collections are allowlisted separately.
- Destructive operations such as drop and delete are blocked.
- Query limits are enforced with `VENUEOPS_MAX_QUERY_LIMIT`.
- Production MongoDB MCP should use a read-only database user.

## Human Approval

The agent may propose operational changes, but staff dispatch, restock requests, signage, facility tickets, and tenant campaigns are created as `pending_approval`. Execution happens only after an operator approves an action.

## Audit Trail

Each action stores:

- rationale
- data used
- SOP evidence IDs
- risk level
- expected impact
- approver
- execution timestamp
- audit events

## Dependency Audit Notes

`npm audit --omit=dev` currently reports two moderate findings through Next.js 15.5.19's transitive `postcss@8.4.31` dependency. The npm-proposed automatic fix downgrades Next.js to 9.3.3, which is a breaking and unsafe mitigation for this app. The app does not stringify untrusted user CSS, and the issue should be rechecked when a Next.js release updates its bundled PostCSS dependency.
