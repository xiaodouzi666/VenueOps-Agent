import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app


client = TestClient(app)


def test_health_and_readiness_routes():
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/healthz").json()["status"] == "ok"

    ready = client.get("/readyz").json()
    assert ready["status"] == "ready"
    assert ready["database"] == "venueops_demo"
