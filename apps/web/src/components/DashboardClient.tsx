"use client";

import { useEffect, useMemo, useState } from "react";
import { Bot, ExternalLink, Map as MapIcon, MessageSquare, ShieldCheck } from "lucide-react";
import { ActionQueue } from "./ActionQueue";
import { BeforeAfter } from "./BeforeAfter";
import { EvidencePanel } from "./EvidencePanel";
import { KpiStrip } from "./KpiStrip";
import { RiskList } from "./RiskList";
import { ScenarioControls } from "./ScenarioControls";
import { ToolTrace } from "./ToolTrace";
import { VenueMap } from "./VenueMap";
import { approveAction, getSnapshot, rejectAction, resetDemo, runAgent, simulateScenario } from "@/lib/api";
import type { AgentRun, Snapshot, ToolTraceStep } from "@/lib/types";

const DEFAULT_MISSION =
  "Kickoff is in 75 minutes. Keep fans moving, avoid stockouts, and handle facility incidents. Propose and execute a safe plan that I can approve.";

export function DashboardClient() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [agentRun, setAgentRun] = useState<AgentRun | null>(null);
  const [mission, setMission] = useState(DEFAULT_MISSION);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trace: ToolTraceStep[] = useMemo(() => {
    if (agentRun?.tool_trace?.length) return agentRun.tool_trace;
    return snapshot?.recent_agent_runs?.[0]?.steps || [];
  }, [agentRun, snapshot]);

  async function refresh() {
    const next = await getSnapshot();
    setSnapshot(next);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  async function runWithBusy(task: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await task();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleRunAgent() {
    await runWithBusy(async () => {
      const result = await runAgent(mission);
      setAgentRun(result);
    });
  }

  if (!snapshot) {
    return (
      <main className="docPage">
        <h1>VenueOps Agent</h1>
        <p>Loading command center...</p>
        {error && <p className="summary">{error}</p>}
      </main>
    );
  }

  const liveActions = new Map(snapshot.actions.map((action) => [action._id, action]));
  const visibleActions = agentRun?.recommended_actions?.length
    ? agentRun.recommended_actions.map((action) => liveActions.get(action._id) || action)
    : snapshot.actions;

  return (
    <div className="appShell">
      <header className="topbar">
        <div className="brand">
          <div className="brandMark"><Bot size={20} /></div>
          <div>
            <h1>VenueOps Agent</h1>
            <p>{snapshot.venue.name} · {snapshot.event.name} · {snapshot.event.status}</p>
          </div>
        </div>
        <nav className="navLinks" aria-label="Primary">
          <a href="#dashboard"><MapIcon size={15} /> Dashboard</a>
          <a href="#agent"><MessageSquare size={15} /> Agent</a>
          <a href="#actions"><ShieldCheck size={15} /> Actions</a>
          <a href="/docs"><ExternalLink size={15} /> Docs</a>
        </nav>
      </header>

      <main className="mainGrid" id="dashboard">
        <div className="leftStack">
          <section className="panel">
            <div className="panelHeader">
              <div>
                <h2>Live Event Command Center</h2>
                <p>World Cup pre-event operations: crowd, queue, inventory, incidents, staff, and actions.</p>
              </div>
              <ScenarioControls
                busy={busy}
                onReset={() => runWithBusy(async () => {
                  setAgentRun(null);
                  await resetDemo();
                })}
                onScenario={(scenario) => runWithBusy(() => simulateScenario(scenario))}
              />
            </div>
            <div className="section">
              <KpiStrip snapshot={snapshot} />
            </div>
            <div className="section">
              <VenueMap zones={snapshot.zone_risks} />
            </div>
            <BeforeAfter snapshot={snapshot} />
          </section>

          <section className="panel" id="agent">
            <div className="panelHeader">
              <div>
                <h2>Agent Mission</h2>
                <p>Runs the observe-analyze-retrieve-plan-confirm loop and creates pending actions.</p>
              </div>
              <span className="pill">{busy ? "running" : "ready"}</span>
            </div>
            <div className="section chatBox">
              <textarea
                className="missionInput"
                value={mission}
                onChange={(event) => setMission(event.target.value)}
                aria-label="Agent mission"
              />
              <div className="buttonRow">
                <button className="button primary" onClick={handleRunAgent} disabled={busy} title="Run VenueOps Agent">
                  <Bot size={16} /> Run Agent
                </button>
                <button className="button ghost" onClick={() => setMission(DEFAULT_MISSION)} disabled={busy} title="Restore demo mission">
                  Restore Mission
                </button>
              </div>
              {error && <div className="summary"><strong>API error</strong>{error}</div>}
              {agentRun && (
                <div className="summary">
                  <strong>{agentRun.required_confirmations} confirmations required</strong>
                  {agentRun.situation_summary}
                  {agentRun.planner && (
                    <p className="miniText muted">
                      Planner: {agentRun.planner.status} via {agentRun.planner.mode}
                      {agentRun.planner.model ? ` · ${agentRun.planner.model}` : ""}
                    </p>
                  )}
                  {agentRun.gemini_note && <p className="miniText muted">{agentRun.gemini_note}</p>}
                </div>
              )}
            </div>
          </section>
        </div>

        <aside className="rightStack">
          <section className="panel">
            <div className="panelHeader">
              <div>
                <h2>Top Risks</h2>
                <p>Deterministic scoring from MongoDB operational collections.</p>
              </div>
            </div>
            <div className="section">
              <RiskList snapshot={snapshot} />
            </div>
          </section>

          <section className="panel" id="actions">
            <div className="panelHeader">
              <div>
                <h2>Action Queue</h2>
                <p>Every operational action requires approval and leaves an audit trail.</p>
              </div>
            </div>
            <div className="section">
              <ActionQueue
                actions={visibleActions}
                busy={busy}
                onApprove={(id) => runWithBusy(() => approveAction(id))}
                onReject={(id) => runWithBusy(() => rejectAction(id))}
              />
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <div>
                <h2>Tool Trace</h2>
                <p>MongoDB MCP Server calls, transport metadata, and controlled writes used by the agent.</p>
              </div>
            </div>
            <div className="section">
              <ToolTrace steps={trace} />
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <div>
                <h2>SOP Evidence</h2>
                <p>Atlas Vector Search-first SOP evidence attached to recommendations.</p>
              </div>
            </div>
            <div className="section">
              <EvidencePanel evidence={agentRun?.evidence || []} />
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}
