import type { AgentRun, Snapshot } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getSnapshot(): Promise<Snapshot> {
  return request<Snapshot>("/api/dashboard/snapshot");
}

export function runAgent(mission: string): Promise<AgentRun> {
  return request<AgentRun>("/api/agent/run", {
    method: "POST",
    body: JSON.stringify({ mission })
  });
}

export function approveAction(actionId: string): Promise<unknown> {
  return request(`/api/actions/${actionId}/approve`, {
    method: "POST",
    body: JSON.stringify({ approver: "demo_operator" })
  });
}

export function rejectAction(actionId: string, reason = "Rejected during demo review."): Promise<unknown> {
  return request(`/api/actions/${actionId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason, actor: "demo_operator" })
  });
}

export function resetDemo(): Promise<unknown> {
  return request("/api/demo/reset", { method: "POST" });
}

export function simulateScenario(scenario: string): Promise<unknown> {
  return request("/api/demo/simulate", {
    method: "POST",
    body: JSON.stringify({ scenario })
  });
}
