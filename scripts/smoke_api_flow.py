#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


API_ROOT = os.environ.get("VENUEOPS_API_ROOT", "http://127.0.0.1:8080").rstrip("/")
WEB_PROXY_ROOT = os.environ.get("VENUEOPS_WEB_PROXY_ROOT", "http://127.0.0.1:3000/api/backend").rstrip("/")
MISSION = "Kickoff is in 75 minutes. Keep fans moving, avoid stockouts, and handle facility incidents."


def request(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read()
        return json.loads(body.decode()) if body else {}


def main() -> None:
    health = request("GET", f"{API_ROOT}/health")
    healthz = request("GET", f"{API_ROOT}/healthz")
    readyz = request("GET", f"{API_ROOT}/readyz")
    web_health = request("GET", f"{WEB_PROXY_ROOT}/health")
    assert health["status"] == "ok", health
    assert healthz["status"] == "ok", healthz
    assert readyz["status"] == "ready", readyz
    assert web_health["status"] == "ok", web_health

    request("POST", f"{API_ROOT}/api/demo/reset")
    request("POST", f"{API_ROOT}/api/demo/simulate", {"scenario": "crowd_surge_gate_b"})
    run = request("POST", f"{API_ROOT}/api/agent/run", {"mission": MISSION})
    tools = [step["tool"] for step in run["tool_trace"]]
    assert len(run["tool_trace"]) >= 11, len(run["tool_trace"])
    assert "gemini.plan" in tools, tools
    assert "mongodb.aggregate" in tools, tools
    assert "mongodb.find" in tools, tools
    assert "mongodb.count" in tools, tools
    assert run["planner"]["ranked_actions"], run["planner"]
    assert len(run["recommended_actions"]) == 5, len(run["recommended_actions"])
    assert run["required_confirmations"] == 5, run["required_confirmations"]

    first, second = run["recommended_actions"][0], run["recommended_actions"][1]
    executed = request("POST", f"{API_ROOT}/api/actions/{first['_id']}/approve", {"approver": "terminal_smoke"})["action"]
    rejected = request(
        "POST",
        f"{API_ROOT}/api/actions/{second['_id']}/reject",
        {"actor": "terminal_smoke", "reason": "Terminal smoke rejection"},
    )["action"]
    assert executed["status"] == "executed", executed
    assert rejected["status"] == "rejected", rejected

    actions = request("GET", f"{API_ROOT}/api/actions")
    assert any(action["_id"] == first["_id"] and action["status"] == "executed" for action in actions["actions"])
    assert any(action["_id"] == second["_id"] and action["status"] == "rejected" for action in actions["actions"])
    assert len(actions["audit"]) >= 2, len(actions["audit"])

    snapshot = request("GET", f"{API_ROOT}/api/dashboard/snapshot")
    before_after = snapshot["kpis"]["before_after"]
    assert before_after["after_pressure"] <= before_after["before_pressure"], before_after
    assert before_after["after_wait_min"] <= before_after["before_wait_min"], before_after

    web_snapshot = request("GET", f"{WEB_PROXY_ROOT}/api/dashboard/snapshot")
    assert web_snapshot["event"]["_id"] == "event_wc_demo_001"

    print(
        json.dumps(
            {
                "status": "terminal smoke passed",
                "api_health": health["status"],
                "api_healthz": healthz["status"],
                "api_readyz": readyz["status"],
                "web_proxy_health": web_health["status"],
                "tool_calls": len(run["tool_trace"]),
                "has_gemini_plan": "gemini.plan" in tools,
                "planner_mode": run["planner"]["mode"],
                "planner_status": run["planner"]["status"],
                "actions": len(run["recommended_actions"]),
                "executed": executed["_id"],
                "rejected": rejected["_id"],
                "audit_events": len(actions["audit"]),
                "pressure_before": before_after["before_pressure"],
                "pressure_after": before_after["after_pressure"],
                "wait_before_min": before_after["before_wait_min"],
                "wait_after_min": before_after["after_wait_min"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
