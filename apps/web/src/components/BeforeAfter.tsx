import type { Snapshot } from "@/lib/types";

function pct(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function BeforeAfter({ snapshot }: { snapshot: Snapshot }) {
  const data = snapshot.kpis.before_after;
  const pressureWidth = Math.min(data.after_pressure * 100, 100);
  const stockWidth = Math.min(data.after_stockout_risk * 45, 100);
  return (
    <div className="section">
      <h2>Before / After KPI</h2>
      <p>Projected impact after approved actions and simulated verification writes.</p>
      <div className="bars" style={{ marginTop: 14 }}>
        <div>
          <div className="rowTop miniText">
            <strong>Gate B pressure</strong>
            <span>{pct(data.before_pressure)} to {pct(data.after_pressure)}</span>
          </div>
          <div className="bar" aria-label="Projected pressure bar">
            <span style={{ width: `${pressureWidth}%` }} />
          </div>
        </div>
        <div>
          <div className="rowTop miniText">
            <strong>Top stockout risk</strong>
            <span>{data.before_stockout_risk.toFixed(1)}x to {data.after_stockout_risk.toFixed(1)}x</span>
          </div>
          <div className="bar" aria-label="Projected stockout bar">
            <span style={{ width: `${stockWidth}%`, background: "var(--amber)" }} />
          </div>
        </div>
      </div>
      <p className="miniText muted" style={{ marginTop: 10 }}>
        Queue wait projection: {data.before_wait_min}m to {data.after_wait_min}m.
      </p>
    </div>
  );
}
