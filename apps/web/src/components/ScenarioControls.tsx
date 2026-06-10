import { Activity, PackageMinus, RotateCcw, Siren, TrendingDown } from "lucide-react";

type Props = {
  busy: boolean;
  onReset: () => void;
  onScenario: (scenario: string) => void;
};

export function ScenarioControls({ busy, onReset, onScenario }: Props) {
  return (
    <div className="buttonRow">
      <button className="button" onClick={onReset} disabled={busy} title="Reset demo data">
        <RotateCcw size={15} /> Reset
      </button>
      <button className="button" onClick={() => onScenario("crowd_surge_gate_b")} disabled={busy} title="Simulate crowd surge">
        <Activity size={15} /> Crowd Surge
      </button>
      <button className="button" onClick={() => onScenario("food_stockout")} disabled={busy} title="Simulate stockout">
        <PackageMinus size={15} /> Stockout
      </button>
      <button className="button" onClick={() => onScenario("facility_incident")} disabled={busy} title="Simulate facility incident">
        <Siren size={15} /> Incident
      </button>
      <button className="button" onClick={() => onScenario("after_actions")} disabled={busy} title="Show after-actions telemetry">
        <TrendingDown size={15} /> After
      </button>
    </div>
  );
}
