import asyncio
"""
Tests unitaires pour le module de polling asynchrone.
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from api.models import Server
from api.poller import poll_server, run_poll_loop


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def server():
    """Retourne un serveur de test standard."""
    return Server(
        id="test-id-123",
        name="test-server",
        host="localhost",
        port=8080,
    )


def make_server(host="localhost", port=8080, name="srv", sid="abc"):
    return Server(id=sid, name=name, host=host, port=port)


# ---------------------------------------------------------------------------
# Tests poll_server — statut UP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_server_status_up(server):
    """Réponse 200 → statut UP."""
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "UP"


@pytest.mark.asyncio
async def test_poll_server_up_updates_status(server):
    """Vérifie que le statut passe de UNKNOWN à UP."""
    assert server.status == "UNKNOWN"
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "UP"


# ---------------------------------------------------------------------------
# Tests poll_server — statut DEGRADED
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_server_status_degraded_on_500(server):
    """Réponse 500 → statut DEGRADED."""
    mock_response = AsyncMock()
    mock_response.status_code = 500

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "DEGRADED"


@pytest.mark.asyncio
async def test_poll_server_status_degraded_on_404(server):
    """Réponse 404 → statut DEGRADED."""
    mock_response = AsyncMock()
    mock_response.status_code = 404

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "DEGRADED"


@pytest.mark.asyncio
async def test_poll_server_status_degraded_on_503(server):
    """Réponse 503 → statut DEGRADED."""
    mock_response = AsyncMock()
    mock_response.status_code = 503

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "DEGRADED"


# ---------------------------------------------------------------------------
# Tests poll_server — statut DOWN
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_server_down_on_connect_error(server):
    """ConnectError → statut DOWN."""
    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "DOWN"


@pytest.mark.asyncio
async def test_poll_server_down_on_timeout(server):
    """TimeoutException → statut DOWN."""
    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "DOWN"


@pytest.mark.asyncio
async def test_poll_server_down_on_request_error(server):
    """RequestError générique → statut DOWN."""
    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.RequestError("Network error")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "DOWN"


@pytest.mark.asyncio
async def test_poll_server_down_on_generic_exception(server):
    """Exception quelconque → statut DOWN."""
    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Unexpected"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

    assert server.status == "DOWN"


# ---------------------------------------------------------------------------
# Tests URL construite
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_server_calls_correct_url(server):
    """Vérifie que poll_server appelle la bonne URL /health."""
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

        mock_client.get.assert_called_once_with(
            "http://localhost:8080/health"
        )


@pytest.mark.asyncio
async def test_poll_server_url_with_different_host():
    """Vérifie l'URL pour un serveur avec host/port différents."""
    server = make_server(host="192.168.1.100", port=443)
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client

        await poll_server(server)

        mock_client.get.assert_called_once_with(
            "http://192.168.1.100:443/health"
        )


# ---------------------------------------------------------------------------
# Tests run_poll_loop
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_poll_loop_empty_servers():
    """run_poll_loop avec dict vide → aucun appel poll_server."""
    servers = {}
    with patch("api.poller.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_sleep.side_effect = [None, asyncio.CancelledError()]
        import asyncio
        try:
            await run_poll_loop(servers)
        except asyncio.CancelledError:
            pass
    # Aucune exception → OK


@pytest.mark.asyncio
async def test_run_poll_loop_calls_poll_server():
    """run_poll_loop appelle poll_server pour chaque serveur."""
    import asyncio
    servers = {
        "id1": make_server(sid="id1", name="s1"),
        "id2": make_server(sid="id2", name="s2", port=9000),
    }

    call_count = 0

    async def mock_poll(server):
        nonlocal call_count
        call_count += 1

    with patch("api.poller.poll_server", side_effect=mock_poll), \
         patch("api.poller.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_sleep.side_effect = [None, asyncio.CancelledError()]
        try:
            await run_poll_loop(servers)
        except asyncio.CancelledError:
            pass

    assert call_count == 2
