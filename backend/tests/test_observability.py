from fastapi.testclient import TestClient

from app.main import app


def test_metrics_exposes_http_counters_without_request_content() -> None:
    client = TestClient(app)
    client.get("/health", headers={"x-request-id": "metrics-test"})

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "ataviva_http_requests_total" in response.text
    assert "metrics-test" not in response.text
