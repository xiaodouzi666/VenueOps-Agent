import type { ZoneRisk } from "@/lib/types";

const fillByStatus: Record<string, string> = {
  normal: "#2f7d5c",
  warning: "#b86e12",
  critical: "#b84536"
};

export function VenueMap({ zones }: { zones: ZoneRisk[] }) {
  return (
    <div className="mapWrap">
      <svg className="venueSvg" viewBox="0 0 820 540" role="img" aria-label="Venue heatmap by zone pressure">
        <rect x="32" y="36" width="756" height="468" rx="8" fill="#f8f7f4" stroke="#d8d2c8" />
        <path d="M62 328H760" stroke="#d8d2c8" strokeWidth="18" strokeLinecap="round" />
        <path d="M62 186H760" stroke="#d8d2c8" strokeWidth="12" strokeLinecap="round" />
        {zones.map((zone) => {
          const map = zone.map || { x: 0, y: 0, w: 100, h: 80 };
          return (
            <g key={zone.zone_id}>
              <rect
                x={map.x}
                y={map.y}
                width={map.w}
                height={map.h}
                rx="8"
                fill={fillByStatus[zone.status]}
                fillOpacity={zone.status === "normal" ? 0.74 : 0.88}
                stroke="#fffefa"
                strokeWidth="3"
              />
              <text x={map.x + 12} y={map.y + 26} fill="#fffefa" fontSize="15" fontWeight="700">
                {zone.zone_name}
              </text>
              <text x={map.x + 12} y={map.y + 50} fill="#fffefa" fontSize="13">
                {Math.round(zone.zone_pressure * 100)}% | {zone.avg_wait_min}m
              </text>
            </g>
          );
        })}
      </svg>
      <div className="zoneList">
        {zones.slice(0, 7).map((zone) => (
          <div className="zoneRow" key={zone.zone_id}>
            <div className="rowTop">
              <strong>{zone.zone_name}</strong>
              <span className={`statusDot status-${zone.status}`} title={zone.status} />
            </div>
            <div className="miniText muted">
              {Math.round(zone.zone_pressure * 100)}% pressure, {zone.avg_wait_min}m wait, gap {zone.staffing_gap}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
