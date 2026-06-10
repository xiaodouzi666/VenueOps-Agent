import { Check, X } from "lucide-react";
import type { Action } from "@/lib/types";

type Props = {
  actions: Action[];
  busy: boolean;
  onApprove: (actionId: string) => void;
  onReject: (actionId: string) => void;
};

function statusClass(status: string) {
  if (status === "executed") return "executed";
  if (status === "rejected") return "rejected";
  if (status === "pending_approval") return "pending";
  return "";
}

export function ActionQueue({ actions, busy, onApprove, onReject }: Props) {
  return (
    <div className="actionList">
      {actions.length === 0 ? (
        <p className="miniText muted">No actions yet. Run the mission to create pending approvals.</p>
      ) : (
        actions.map((action) => (
          <div className="actionCard" key={action._id}>
            <div className="actionTitle">
              <strong>{action.title}</strong>
              <span className={`pill ${statusClass(action.status)}`}>{action.status}</span>
            </div>
            <div className="actionMeta">
              <p><strong>Why now:</strong> {action.rationale}</p>
              <p><strong>Data used:</strong> {action.data_used.join(", ")}</p>
              <p><strong>Risk:</strong> {action.risk_level}</p>
              <p><strong>Expected impact:</strong> {action.expected_impact}</p>
            </div>
            {action.audit?.length ? (
              <div className="auditTrail" aria-label={`Audit trail for ${action.title}`}>
                <strong>Audit trail</strong>
                {action.audit.slice(-3).map((entry) => (
                  <p key={`${action._id}-${entry.event}-${entry.created_at}`}>
                    <span>{entry.event}</span> by {entry.actor} · {entry.created_at}
                  </p>
                ))}
              </div>
            ) : null}
            {action.status === "pending_approval" && (
              <div className="buttonRow" style={{ marginTop: 12 }}>
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={() => onApprove(action._id)}
                  title="Approve and execute action"
                  aria-label={`Approve ${action.title}`}
                >
                  <Check size={15} /> Approve
                </button>
                <button
                  className="button danger"
                  disabled={busy}
                  onClick={() => onReject(action._id)}
                  title="Reject action"
                  aria-label={`Reject ${action.title}`}
                >
                  <X size={15} /> Reject
                </button>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}
