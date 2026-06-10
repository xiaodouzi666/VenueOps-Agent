import { Activity, AlertTriangle, CheckCircle2, Clock3, PackageSearch, Users } from "lucide-react";
import type { Snapshot } from "@/lib/types";

function pct(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function KpiStrip({ snapshot }: { snapshot: Snapshot }) {
  const kpis = snapshot.kpis;
  return (
    <div className="kpiGrid">
      <div className="kpi">
        <label><AlertTriangle size={14} /> Overall Risk</label>
        <strong>{kpis.overall_risk}</strong>
        <span>Current demo state</span>
      </div>
      <div className="kpi">
        <label><Users size={14} /> Crowd Risk</label>
        <strong>{pct(kpis.crowd_risk)}</strong>
        <span>Riskiest zone pressure</span>
      </div>
      <div className="kpi">
        <label><Clock3 size={14} /> Longest Wait</label>
        <strong>{kpis.longest_wait_min}m</strong>
        <span>Queue SLA is 15m</span>
      </div>
      <div className="kpi">
        <label><PackageSearch size={14} /> Stockout Risks</label>
        <strong>{kpis.stockout_risks}</strong>
        <span>Warning or critical SKUs</span>
      </div>
      <div className="kpi">
        <label><Activity size={14} /> Open Incidents</label>
        <strong>{kpis.open_incidents}</strong>
        <span>Facility and crowd issues</span>
      </div>
      <div className="kpi">
        <label><CheckCircle2 size={14} /> Executed</label>
        <strong>{kpis.executed_actions}</strong>
        <span>{kpis.pending_actions} pending approval</span>
      </div>
    </div>
  );
}
