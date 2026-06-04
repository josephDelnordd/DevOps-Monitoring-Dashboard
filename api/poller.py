"""
Module de polling asynchrone pour vérifier la santé des serveurs.
"""
import asyncio
import logging
from typing import Dict

import httpx

from api.models import Server

logger = logging.getLogger(__name__)

POLL_INTERVAL = 10
REQUEST_TIMEOUT = 5.0


async def poll_server(server: Server) -> None:
    """
    Teste l'endpoint GET /health d'un serveur et met à jour son statut.

    Status possibles :
    - UP       : réponse 200 reçue
    - DEGRADED : réponse HTTP mais code != 200
    - DOWN     : pas de réponse (timeout, connexion refusée)

    Args:
        server: Instance Server à tester et mettre à jour.
    """
    url = f"{server.base_url()}/health"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url)
            if response.status_code == 200:
                server.status = "UP"
            else:
                server.status = "DEGRADED"
            logger.info(
                "Polled %s (%s) → %s [HTTP %d]",
                server.name,
                url,
                server.status,
                response.status_code,
            )
    except Exception as exc:
        server.status = "DOWN"
        logger.warning(
            "Polled %s (%s) → DOWN (%s)",
            server.name,
            url,
            exc,
        )


async def run_poll_loop(servers: Dict[str, Server]) -> None:
    """
    Boucle infinie qui poll tous les serveurs enregistrés toutes les
    POLL_INTERVAL secondes.

    Args:
        servers: Dictionnaire {server_id: Server} partagé avec l'app.
    """
    logger.info("Poll loop started (interval=%ds)", POLL_INTERVAL)
    while True:
        if servers:
            await asyncio.gather(
                *[poll_server(s) for s in servers.values()]
            )
        await asyncio.sleep(POLL_INTERVAL)
