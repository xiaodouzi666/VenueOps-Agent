import { DatabaseZap } from "lucide-react";
import type { ToolTraceStep } from "@/lib/types";

export function ToolTrace({ steps }: { steps: ToolTraceStep[] }) {
  return (
    <div className="traceList">
      {steps.length === 0 ? (
        <p className="miniText muted">Run the agent to see MongoDB MCP calls.</p>
      ) : (
        steps.map((step, index) => (
          <div className="traceRow" key={`${step.tool}-${index}`}>
            <span className="traceTool"><DatabaseZap size={14} /> {step.tool}</span>
            <div>
              <strong className="miniText">{step.collection}</strong>
              <div className="miniText muted">{step.purpose}</div>
              <div className="traceTransport miniText">transport: {step.transport}</div>
            </div>
            <span className="pill">{step.status} · {step.duration_ms}ms</span>
          </div>
        ))
      )}
    </div>
  );
}
