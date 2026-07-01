import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(scope="module")
def client():
    return TestClient(main.app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "version" in body
    assert "documents" in body and "chunks" in body


@pytest.mark.parametrize("payload", [
    {"question": "   "},                       # empty after strip
    {"question": ""},                          # too short
    {"question": "ok", "search_mode": "bogus"},  # invalid mode
    {"question": "ok", "alpha": 5},              # out of range
    {"question": "ok", "n_results": 999},        # out of range
])
def test_query_validation_rejects_bad_requests(client, payload):
    r = client.post("/api/query", json=payload)
    assert r.status_code == 422


def test_query_requires_documents_field(client):
    r = client.post("/api/query", json={})  # missing question
    assert r.status_code == 422
