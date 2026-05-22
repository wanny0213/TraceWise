import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from tracewise.api.app import app
from tracewise.ingestion.bundles import load_incident_bundle


def test_triage_api_returns_report():
    client = TestClient(app)
    bundle = load_incident_bundle("incidents/demo-auth-regression")

    response = client.post(
        "/triage",
        json={"incident": bundle.model_dump(), "query": "Why did login fail?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["incident_id"] == "demo-auth-regression"
    assert body["hypotheses"]
