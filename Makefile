# =============================================================================
# DevOps Monitor — Makefile
# =============================================================================

.PHONY: up down logs test lint dev clean help

# Variables
COMPOSE = docker compose
PYTEST  = pytest tests/ -v --cov=api --cov-fail-under=75

# ---------------------------------------------------------------------------
# Stack Docker
# ---------------------------------------------------------------------------

## Démarre la stack complète en arrière-plan
up:
	$(COMPOSE) up --build -d

## Arrête la stack et supprime les volumes
down:
	$(COMPOSE) down -v

## Affiche les logs en temps réel
logs:
	$(COMPOSE) logs -f

## Redémarre la stack
restart: down up

# ---------------------------------------------------------------------------
# Qualité du code
# ---------------------------------------------------------------------------

## Lance les tests avec coverage
test:
	$(PYTEST)

## Lance le linter flake8
lint:
	flake8 api/ dashboard/ tests/ --max-line-length=88

## Lance les tests + lint
check: lint test

# ---------------------------------------------------------------------------
# Développement local (sans Docker)
# ---------------------------------------------------------------------------

## Lance l'API et le dashboard en local (nécessite .env sourcé)
dev:
	@echo "Démarrage de l'API sur http://localhost:8000 ..."
	@echo "Démarrage du Dashboard sur http://localhost:8501 ..."
	@trap 'kill %1 %2' INT; \
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload & \
	streamlit run dashboard/app.py \
		--server.port=8501 \
		--server.address=0.0.0.0 \
		--browser.gatherUsageStats=false & \
	wait

## Lance uniquement l'API en mode reload
dev-api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

## Lance uniquement le dashboard
dev-dashboard:
	streamlit run dashboard/app.py \
		--server.port=8501 \
		--server.address=0.0.0.0 \
		--browser.gatherUsageStats=false

# ---------------------------------------------------------------------------
# Nettoyage
# ---------------------------------------------------------------------------

## Supprime les fichiers de cache Python et de tests
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/

## Affiche l'aide
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## //'
