from app.db.mongo import get_repository
from app.tools.risk_tools import compute_inventory_risk, compute_zone_risk, get_current_event_snapshot


def test_gate_b_is_critical_highest_zone_risk():
    repo = get_repository(force_memory=True)
    risks = compute_zone_risk(repo, "event_wc_demo_001")

    assert risks[0]["zone_id"] == "gate_b"
    assert risks[0]["status"] == "critical"
    assert risks[0]["zone_pressure"] > 0.9
    assert risks[0]["avg_wait_min"] == 18


def test_inventory_stockout_risk_flags_priority_skus():
    repo = get_repository(force_memory=True)
    inventory = compute_inventory_risk(repo, "event_wc_demo_001")

    assert inventory[0]["status"] == "critical"
    assert inventory[0]["stockout_risk"] > 1
    assert any(item["sku"] == "water_500ml" for item in inventory)


def test_snapshot_contains_p1_dashboard_surfaces():
    repo = get_repository(force_memory=True)
    snapshot = get_current_event_snapshot(repo, "event_wc_demo_001")

    assert snapshot["kpis"]["overall_risk"] in {"warning", "critical"}
    assert snapshot["zone_risks"]
    assert snapshot["inventory_risks"]
    assert snapshot["incident_priorities"]
