"""
Modèles de données pour le monitoring des serveurs.
"""
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, field_validator


@dataclass
class Server:
    """
    Représente un serveur enregistré dans le système de monitoring.

    Attributes:
        id: Identifiant unique du serveur.
        name: Nom lisible du serveur.
        host: Adresse IP ou hostname du serveur.
        port: Port de l'endpoint /health du serveur.
        status: Statut courant (UNKNOWN, UP, DEGRADED, DOWN).
    """
    id: str
    name: str
    host: str
    port: int
    status: str = "UNKNOWN"

    def base_url(self) -> str:
        """
        Retourne l'URL de base du serveur.

        Returns:
            str: URL au format http://host:port
        """
        return f"http://{self.host}:{self.port}"


class ServerIn(BaseModel):
    """
    Schéma Pydantic pour la création d'un serveur (entrée).

    Attributes:
        name: Nom du serveur.
        host: Adresse IP ou hostname.
        port: Port entre 1 et 65535.
    """
    name: str
    host: str
    port: int

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Valide que le port est dans la plage 1-65535."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class ServerOut(BaseModel):
    """
    Schéma Pydantic pour la réponse serveur (sortie).

    Attributes:
        id: Identifiant unique.
        name: Nom du serveur.
        host: Adresse IP ou hostname.
        port: Port du serveur.
        status: Statut courant.
        base_url: URL de base construite.
    """
    id: str
    name: str
    host: str
    port: int
    status: str
    base_url: Optional[str] = None

    model_config = {"from_attributes": True}
