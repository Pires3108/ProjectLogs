from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_request_id() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-request-id"]


def test_capabilities_exposes_profiles_and_profile_specific_toggles() -> None:
    response = client.get("/v1/capabilities")

    assert response.status_code == 200
    profiles = {item["perfil"]: item["toggles_permitidos"] for item in response.json()["perfis"]}
    assert set(profiles) == {"estudo", "organizacao", "backlog"}
    assert "exercicios" in profiles["estudo"]
    assert "exercicios" not in profiles["organizacao"]
    assert "linha_do_tempo" in profiles["organizacao"]


def test_configuration_endpoint_returns_effective_toggles_and_warnings() -> None:
    response = client.post(
        "/v1/document-configurations/validate",
        json={
            "perfil": "organizacao",
            "toggles": {"exercicios": True, "linha_do_tempo": True},
        },
    )

    assert response.status_code == 200
    assert response.json()["toggles"]["exercicios"] is False
    assert response.json()["toggles"]["linha_do_tempo"] is True
    assert response.json()["avisos"][0]["toggle"] == "exercicios"
