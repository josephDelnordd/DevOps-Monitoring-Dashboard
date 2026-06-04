"""
Module d'authentification par API Key pour FastAPI.
"""
import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dépendance FastAPI qui vérifie la clé API dans le header X-API-Key.

    La clé valide est chargée depuis la variable d'environnement API_KEY.

    Args:
        api_key: Valeur du header X-API-Key.

    Returns:
        str: La clé API validée.

    Raises:
        HTTPException: 403 si la clé est absente ou invalide.
    """
    expected_key = os.getenv("API_KEY", "")

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key",
        )
    return api_key
