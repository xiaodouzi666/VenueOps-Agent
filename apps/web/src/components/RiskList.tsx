import type { Snapshot } from "@/lib/types";

export function RiskList({ snapshot }: { snapshot: Snapshot }) {
  return (
    <div className="riskList">
      {snapshot.zone_risks.slice(0, 3).map((zone) => (
        <div className="riskRow" key={zone.zone_id}>
          <div className="rowTop">
            <strong>{zone.zone_name}</strong>
            <span className={`statusDot status-${zone.status}`} />
          </div>
          <p className="miniText muted">{zone.explanation}</p>
        </div>
      ))}
      {snapshot.inventory_risks.slice(0, 2).map((item) => (
        <div className="riskRow" key={item.inventory_id}>
          <div className="rowTop">
            <strong>{item.name}</strong>
            <span className={`statusDot status-${item.status}`} />
          </div>
          <p className="miniText muted">{item.explanation}</p>
        </div>
      ))}
      {snapshot.incident_priorities.slice(0, 2).map((incident) => (
        <div className="riskRow" key={incident._id}>
          <div className="rowTop">
            <strong>{incident.zone_name}</strong>
            <span className="pill">{incident.severity}</span>
          </div>
          <p className="miniText muted">{incident.description}</p>
        </div>
      ))}
    </div>
  );
}
