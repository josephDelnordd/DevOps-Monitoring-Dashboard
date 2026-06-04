"""
Application FastAPI principale — DevOps Monitoring Dashboard.

Endpoints :
    GET  /health              → liveness probe
    GET  /metrics             → métriques système (CPU, mémoire, disque)
    WS   /ws/metrics          → stream JSON toutes les secondes
    POST /servers             → enregistrer un serveur (API key requise)
    GET  /servers             → lister les serveurs + statut
    DELETE /servers/{id}      → supprimer un serveur (API key requise)
    POST /servers/{id}/check  → health check manuel (API key requise)
"""
import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from api.auth import verify_api_key
from api.metrics import get_system_metrics
from api.models import Server, ServerIn, ServerOut
from api.poller import poll_server, run_poll_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stockage en mémoire des serveurs enregistrés
servers: Dict[str, Server] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    Lance la boucle de polling au démarrage.
    """
    logger.info("Starting DevOps Monitor API...")
    poll_task = asyncio.create_task(run_poll_loop(servers))
    try:
        yield
    finally:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            logger.info("Poll loop stopped.")


app = FastAPI(
    title="DevOps Monitor API",
    description="API de monitoring temps réel pour DevOps",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Routes publiques
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Liveness probe.

    Returns:
        dict: {"status": "ok"}
    """
    return {"status": "ok"}


@app.get("/metrics", tags=["Metrics"])
async def get_metrics() -> dict:
    """
    Retourne les métriques système courantes (CPU, mémoire, disque).

    Returns:
        dict: Snapshot des métriques via psutil.
    """
    return get_system_metrics()


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket) -> None:
    """
    Stream WebSocket qui envoie les métriques JSON toutes les secondes.

    Gère proprement la déconnexion du client.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            metrics = get_system_metrics()
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        await websocket.close()


# ---------------------------------------------------------------------------
# Routes Serveurs (protégées par API Key)
# ---------------------------------------------------------------------------


@app.post(
    "/servers",
    response_model=ServerOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Servers"],
    dependencies=[Depends(verify_api_key)],
)
async def create_server(server_in: ServerIn) -> ServerOut:
    """
    Enregistre un nouveau serveur dans le système de monitoring.

    Args:
        server_in: Données du serveur (name, host, port).

    Returns:
        ServerOut: Serveur créé avec son ID et statut initial.
    """
    server_id = str(uuid.uuid4())
    server = Server(
        id=server_id,
        name=server_in.name,
        host=server_in.host,
        port=server_in.port,
    )
    servers[server_id] = server
    logger.info("Server registered: %s (%s)", server.name, server_id)
    return ServerOut(
        id=server.id,
        name=server.name,
        host=server.host,
        port=server.port,
        status=server.status,
        base_url=server.base_url(),
    )


@app.get("/servers", response_model=List[ServerOut], tags=["Servers"])
async def list_servers() -> List[ServerOut]:
    """
    Liste tous les serveurs enregistrés avec leur statut courant.

    Returns:
        List[ServerOut]: Liste des serveurs.
    """
    return [
        ServerOut(
            id=s.id,
            name=s.name,
            host=s.host,
            port=s.port,
            status=s.status,
            base_url=s.base_url(),
        )
        for s in servers.values()
    ]


@app.delete(
    "/servers/{server_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Servers"],
    dependencies=[Depends(verify_api_key)],
)
async def delete_server(server_id: str) -> None:
    """
    Supprime un serveur du système de monitoring.

    Args:
        server_id: Identifiant unique du serveur.

    Raises:
        HTTPException: 404 si le serveur n'existe pas.
    """
    if server_id not in servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )
    del servers[server_id]
    logger.info("Server deleted: %s", server_id)


@app.post(
    "/servers/{server_id}/check",
    response_model=ServerOut,
    tags=["Servers"],
    dependencies=[Depends(verify_api_key)],
)
async def manual_health_check(server_id: str) -> ServerOut:
    """
    Déclenche un health check manuel immédiat sur un serveur.

    Args:
        server_id: Identifiant unique du serveur.

    Returns:
        ServerOut: Serveur avec le statut mis à jour.

    Raises:
        HTTPException: 404 si le serveur n'existe pas.
    """
    if server_id not in servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )
    server = servers[server_id]
    await poll_server(server)
    logger.info(
        "Manual check for %s → %s", server.name, server.status
    )
    return ServerOut(
        id=server.id,
        name=server.name,
        host=server.host,
        port=server.port,
        status=server.status,
        base_url=server.base_url(),
    )
