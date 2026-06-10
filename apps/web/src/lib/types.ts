export type Status = "normal" | "warning" | "critical";

export type ZoneRisk = {
  zone_id: string;
  zone_name: string;
  zone_type: string;
  people_count: number;
  safe_capacity: number;
  zone_pressure: number;
  queue_length: number;
  avg_wait_min: number;
  queue_risk: number;
  required_staff: number;
  available_staff: number;
  staffing_gap: number;
  priority_score: number;
  status: Status;
  map?: { x: number; y: number; w: number; h: number };
  explanation: string;
};

export type InventoryRisk = {
  inventory_id: string;
  tenant_name: string;
  tenant_id: string;
  zone_id: string;
  sku: string;
  name: string;
  current_stock: number;
  projected_next_90min: number;
  stockout_risk: number;
  status: Status;
  explanation: string;
};

export type Incident = {
  _id: string;
  zone_name: string;
  zone_id: string;
  type: string;
  severity: string;
  description: string;
  status: string;
  priority_score: number;
  explanation: string;
};

export type Action = {
  _id: string;
  event_id: string;
  type: string;
  title: string;
  rationale: string;
  risk_level: string;
  status: string;
  payload: Record<string, unknown>;
  data_used: string[];
  expected_impact: string;
  evidence_doc_ids: string[];
  created_at: string;
  approved_by?: string | null;
  executed_at?: string | null;
  audit?: Array<{
    event: string;
    actor: string;
    created_at: string;
    details?: Record<string, unknown>;
  }>;
};

export type ToolTraceStep = {
  tool: string;
  collection: string;
  purpose: string;
  status: string;
  duration_ms: number;
  transport: string;
  output?: Record<string, unknown>;
  evidence_ids?: string[];
};

export type EvidenceDoc = {
  _id: string;
  title: string;
  doc_type: string;
  content: string;
  tags: string[];
  score: number;
  retrieval_mode: string;
};

export type Snapshot = {
  event: { _id: string; name: string; start_time: string; expected_attendance: number; status: string };
  venue: { name: string; city: string; capacity: number; timezone: string };
  zone_risks: ZoneRisk[];
  inventory_risks: InventoryRisk[];
  incident_priorities: Incident[];
  actions: Action[];
  recent_agent_runs: Array<{ _id: string; plan_summary: string; steps: ToolTraceStep[]; created_at: string }>;
  kpis: {
    overall_risk: string;
    crowd_risk: number;
    longest_wait_min: number;
    stockout_risks: number;
    open_incidents: number;
    pending_actions: number;
    executed_actions: number;
    before_after: {
      before_pressure: number;
      after_pressure: number;
      before_wait_min: number;
      after_wait_min: number;
      before_stockout_risk: number;
      after_stockout_risk: number;
    };
  };
};

export type AgentRun = {
  situation_summary: string;
  key_risks: Array<{ risk: string; severity: string; evidence: string[] }>;
  recommended_actions: Action[];
  required_confirmations: number;
  evidence: EvidenceDoc[];
  tool_trace: ToolTraceStep[];
  planner?: {
    status: string;
    mode: string;
    model?: string;
    summary: string;
    ranked_actions: Array<{
      type: string;
      title: string;
      rationale: string;
      risk_level: string;
      evidence_doc_ids: string[];
    }>;
    constraints: string[];
    verification_focus: string[];
    reason?: string;
  };
  agent_run_id: string;
  gemini_note?: string | null;
};
