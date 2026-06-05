"""
Tests d'intégration pour les routes FastAPI.
"""
import os
import httpx
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

os.environ["API_KEY"] = "test-secret-key"

from api.main import app, servers  # noqa: E402

TEST_API_KEY = "test-secret-key"
HEADERS = {"X-API-Key": TEST_API_KEY}
SERVER_PAYLOAD = {"name": "prod-api", "host": "192.168.1.1", "port": 8000}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_servers():
    """Vide le dictionnaire des serveurs avant/après chaque test."""
    servers.clear()
    yield
    servers.clear()


@pytest.fixture
def created_server(client):
    """Crée un serveur et retourne la réponse JSON."""
    response = client.post("/servers", json=SERVER_PAYLOAD, headers=HEADERS)
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# Tests /health
# ---------------------------------------------------------------------------


def test_health_returns_ok(client):
    """GET /health doit retourner {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Tests /metrics
# ---------------------------------------------------------------------------


def test_metrics_status_code(client):
    """GET /metrics doit retourner 200."""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_required_fields(client):
    """GET /metrics doit contenir tous les champs obligatoires."""
    response = client.get("/metrics")
    data = response.json()
    for field in ["cpu_percent", "memory_percent", "disk_percent",
                  "memory_total_gb", "memory_used_gb",
                  "disk_total_gb", "disk_used_gb"]:
        assert field in data, f"Champ manquant : {field}"


def test_metrics_values_in_range(client):
    """Les pourcentages doivent être entre 0 et 100."""
    response = client.get("/metrics")
    data = response.json()
    assert 0 <= data["cpu_percent"] <= 100
    assert 0 <= data["memory_percent"] <= 100
    assert 0 <= data["disk_percent"] <= 100


def test_metrics_gb_values_positive(client):
    """Les valeurs GB doivent être positives."""
    data = client.get("/metrics").json()
    assert data["memory_total_gb"] > 0
    assert data["disk_total_gb"] > 0


# ---------------------------------------------------------------------------
# Tests authentification
# ---------------------------------------------------------------------------


def test_post_server_without_api_key_returns_403(client):
    """POST /servers sans API Key → 403."""
    response = client.post("/servers", json=SERVER_PAYLOAD)
    assert response.status_code == 403


def test_post_server_with_wrong_api_key_returns_403(client):
    """POST /servers avec mauvaise API Key → 403."""
    response = client.post(
        "/servers", json=SERVER_PAYLOAD,
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 403


def test_delete_server_without_api_key_returns_403(client):
    """DELETE /servers/{id} sans API Key → 403."""
    response = client.delete("/servers/some-id")
    assert response.status_code == 403


def test_manual_check_without_api_key_returns_403(client):
    """POST /servers/{id}/check sans API Key → 403."""
    response = client.post("/servers/some-id/check")
    assert response.status_code == 403


def test_manual_check_wrong_api_key_returns_403(client):
    """POST /servers/{id}/check avec mauvaise clé → 403."""
    response = client.post(
        "/servers/some-id/check",
        headers={"X-API-Key": "bad-key"}
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tests POST /servers
# ---------------------------------------------------------------------------


def test_create_server_returns_201(client):
    """POST /servers → 201 avec les données correctes."""
    response = client.post("/servers", json=SERVER_PAYLOAD, headers=HEADERS)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "prod-api"
    assert data["host"] == "192.168.1.1"
    assert data["port"] == 8000
    assert "id" in data
    assert data["status"] == "UNKNOWN"


def test_create_server_base_url_in_response(client):
    """La réponse doit contenir le bon base_url."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "example.com", "port": 9000},
        headers=HEADERS,
    )
    assert response.json()["base_url"] == "http://example.com:9000"


def test_create_server_invalid_port(client):
    """POST /servers avec port > 65535 → 422."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 99999},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_create_server_port_zero(client):
    """POST /servers avec port=0 → 422."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 0},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_create_server_port_negative(client):
    """POST /servers avec port négatif → 422."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": -1},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_create_server_port_max_valid(client):
    """POST /servers avec port=65535 → 201."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 65535},
        headers=HEADERS,
    )
    assert response.status_code == 201


def test_create_server_port_min_valid(client):
    """POST /servers avec port=1 → 201."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 1},
        headers=HEADERS,
    )
    assert response.status_code == 201


def test_create_multiple_servers(client):
    """Créer plusieurs serveurs → chacun a un ID unique."""
    ids = []
    for i in range(3):
        r = client.post(
            "/servers",
            json={"name": f"srv-{i}", "host": "localhost", "port": 8000 + i},
            headers=HEADERS,
        )
        assert r.status_code == 201
        ids.append(r.json()["id"])
    assert len(set(ids)) == 3  # tous les IDs sont uniques


# ---------------------------------------------------------------------------
# Tests GET /servers
# ---------------------------------------------------------------------------


def test_list_servers_empty(client):
    """GET /servers → liste vide au départ."""
    response = client.get("/servers")
    assert response.status_code == 200
    assert response.json() == []


def test_list_servers_after_creation(client):
    """GET /servers → liste avec 2 serveurs après création."""
    client.post("/servers",
                json={"name": "s1", "host": "10.0.0.1", "port": 80},
                headers=HEADERS)
    client.post("/servers",
                json={"name": "s2", "host": "10.0.0.2", "port": 443},
                headers=HEADERS)
    response = client.get("/servers")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_servers_contains_required_fields(client, created_server):
    """Chaque serveur listé doit avoir les champs obligatoires."""
    response = client.get("/servers")
    data = response.json()
    assert len(data) == 1
    server = data[0]
    for field in ["id", "name", "host", "port", "status", "base_url"]:
        assert field in server, f"Champ manquant : {field}"


# ---------------------------------------------------------------------------
# Tests DELETE /servers/{id}
# ---------------------------------------------------------------------------


def test_delete_server_success(client, created_server):
    """DELETE /servers/{id} → 204 et serveur supprimé."""
    server_id = created_server["id"]
    response = client.delete(f"/servers/{server_id}", headers=HEADERS)
    assert response.status_code == 204
    assert client.get("/servers").json() == []


def test_delete_server_not_found(client):
    """DELETE /servers/{id} inexistant → 404."""
    response = client.delete("/servers/nonexistent-id", headers=HEADERS)
    assert response.status_code == 404


def test_delete_server_twice(client, created_server):
    """Supprimer deux fois le même serveur → 404 au second appel."""
    server_id = created_server["id"]
    client.delete(f"/servers/{server_id}", headers=HEADERS)
    response = client.delete(f"/servers/{server_id}", headers=HEADERS)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests POST /servers/{id}/check
# ---------------------------------------------------------------------------


def test_manual_check_not_found(client):
    """POST /servers/{id}/check avec ID inexistant → 404."""
    response = client.post("/servers/nonexistent-id/check", headers=HEADERS)
    assert response.status_code == 404


def test_manual_check_server_up(client, created_server):
    """POST /servers/{id}/check → 200 avec statut UP si serveur répond."""
    server_id = created_server["id"]

    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("api.poller.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.post(f"/servers/{server_id}/check", headers=HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["id"] == server_id


def test_manual_check_server_degraded(client, created_server):
    """POST /servers/{id}/check → statut DEGRADED si code != 200."""
    server_id = created_server["id"]

    mock_response = AsyncMock()
    mock_response.status_code = 503

    with patch("api.poller.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.post(f"/servers/{server_id}/check", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["status"] == "DEGRADED"


def test_manual_check_server_down(client, created_server):
    """POST /servers/{id}/check → statut DOWN si exception réseau."""
    server_id = created_server["id"]

    with patch("api.poller.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.RequestError("Connection refused")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.post(f"/servers/{server_id}/check", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["status"] == "DOWN"
