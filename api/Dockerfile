# =============================================================================
# Stage 1 — Builder : installation des dépendances
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Copier uniquement requirements pour profiter du cache Docker
COPY requirements.txt .

# Installer les dépendances dans un répertoire isolé
RUN pip install --upgrade pip \
	&& pip install --no-cache-dir \
	--prefix=/install \
	-r requirements.txt

# =============================================================================
# Stage 2 — Runtime : image légère sans pip ni outils de build
# =============================================================================
FROM python:3.11-slim AS runtime

# Métadonnées
LABEL maintainer="DevOps Monitor" \
	version="1.0.0" \
	description="FastAPI backend for DevOps Monitoring Dashboard"

WORKDIR /app

# Copier les dépendances installées depuis le builder
COPY --from=builder /install /usr/local

# Copier le code source de l'API
COPY api/ ./api/

# Créer un utilisateur non-root pour la sécurité
RUN adduser --disabled-password --gecos "" appuser \
	&& chown -R appuser:appuser /app
USER appuser

# Port exposé
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
	CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Commande de démarrage
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
