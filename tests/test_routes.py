"""
Tests d'intégration pour les routes FastAPI.
"""
import os
import pytest
from fastapi.testclient import TestClient

# Définir l'API Key avant d'importer l'app
os.environ["API_KEY"] = "test-secret-key"

from api.main import app, servers  # noqa: E402

client = TestClient(app)
HEADERS = {"X-API-Key": "test-secret-key"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_servers():
    """Vide le dictionnaire des serveurs avant chaque test."""
    servers.clear()
    yield
    servers.clear()


# ---------------------------------------------------------------------------
# Tests /health
# ---------------------------------------------------------------------------


def test_health_returns_ok():
    """GET /health doit retourner {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Tests /metrics
# ---------------------------------------------------------------------------


def test_metrics_status_code():
    """GET /metrics doit retourner 200."""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_fields():
    """GET /metrics doit contenir les champs obligatoires."""
    response = client.get("/metrics")
    data = response.json()
    assert "cpu_percent" in data
    assert "memory_percent" in data
    assert "disk_percent" in data


def test_metrics_values_in_range():
    """Les métriques doivent être dans des plages valides."""
    response = client.get("/metrics")
    data = response.json()
    assert 0 <= data["cpu_percent"] <= 100
    assert 0 <= data["memory_percent"] <= 100
    assert 0 <= data["disk_percent"] <= 100


# ---------------------------------------------------------------------------
# Tests authentification
# ---------------------------------------------------------------------------


def test_post_server_without_api_key_returns_403():
    """POST /servers sans API Key doit retourner 403."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 8080},
    )
    assert response.status_code == 403


def test_post_server_with_wrong_api_key_returns_403():
    """POST /servers avec une mauvaise API Key doit retourner 403."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 8080},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 403


def test_delete_server_without_api_key_returns_403():
    """DELETE /servers/{id} sans API Key doit retourner 403."""
    response = client.delete("/servers/some-id")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tests CRUD /servers
# ---------------------------------------------------------------------------


def test_create_server_returns_201():
    """POST /servers doit retourner 201 avec les données du serveur."""
    response = client.post(
        "/servers",
        json={"name": "prod-api", "host": "192.168.1.1", "port": 8000},
        headers=HEADERS,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "prod-api"
    assert data["host"] == "192.168.1.1"
    assert data["port"] == 8000
    assert "id" in data
    assert data["status"] == "UNKNOWN"


def test_create_server_invalid_port():
    """POST /servers avec un port invalide doit retourner 422."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 99999},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_create_server_port_zero():
    """POST /servers avec port=0 doit retourner 422."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 0},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_list_servers_empty():
    """GET /servers doit retourner une liste vide initialement."""
    response = client.get("/servers")
    assert response.status_code == 200
    assert response.json() == []


def test_list_servers_after_creation():
    """GET /servers doit lister les serveurs créés."""
    client.post(
        "/servers",
        json={"name": "server-1", "host": "10.0.0.1", "port": 80},
        headers=HEADERS,
    )
    client.post(
        "/servers",
        json={"name": "server-2", "host": "10.0.0.2", "port": 443},
        headers=HEADERS,
    )
    response = client.get("/servers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_delete_server_success():
    """DELETE /servers/{id} doit retourner 204."""
    create = client.post(
        "/servers",
        json={"name": "to-delete", "host": "1.1.1.1", "port": 8080},
        headers=HEADERS,
    )
    server_id = create.json()["id"]

    response = client.delete(
        f"/servers/{server_id}", headers=HEADERS
    )
    assert response.status_code == 204

    # Vérifie que le serveur est bien supprimé
    list_response = client.get("/servers")
    assert len(list_response.json()) == 0


def test_delete_server_not_found():
    """DELETE /servers/{id} avec un ID inexistant doit retourner 404."""
    response = client.delete(
        "/servers/nonexistent-id", headers=HEADERS
    )
    assert response.status_code == 404


def test_manual_check_not_found():
    """POST /servers/{id}/check avec un ID inexistant doit retourner 404."""
    response = client.post(
        "/servers/nonexistent-id/check", headers=HEADERS
    )
    assert response.status_code == 404


def test_server_base_url_in_response():
    """La réponse doit contenir le champ base_url."""
    response = client.post(
        "/servers",
        json={"name": "url-test", "host": "example.com", "port": 9000},
        headers=HEADERS,
    )
    data = response.json()
    assert data["base_url"] == "http://example.com:9000"
