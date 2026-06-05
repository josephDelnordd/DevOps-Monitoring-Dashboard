# =============================================================================
# DevOps Monitor — Makefile
# =============================================================================

.PHONY: init up down logs test lint dev dev-api dev-dashboard clean kill-ports help \
        check restart

# Variables
COMPOSE  = docker compose
PYTEST   = pytest tests/ -v --cov=api --cov-fail-under=75
PYTHON   = python3.13
VENV     = .venv
VENV_BIN = $(VENV)/bin

# Détection OS (Windows vs Unix)
ifeq ($(OS), Windows_NT)
	VENV_ACTIVATE = $(VENV)/Scripts/activate
	VENV_PYTHON   = $(VENV)/Scripts/python
	VENV_PIP      = $(VENV)/Scripts/pip
else
	VENV_ACTIVATE = $(VENV)/bin/activate
	VENV_PYTHON   = $(VENV)/bin/python
	VENV_PIP      = $(VENV)/bin/pip
endif

# =============================================================================
# INITIALISATION
# =============================================================================

## Initialise le projet complet (venv + dépendances + .env)
init:
	@echo "🚀 Initialisation du projet DevOps Monitor..."
	@echo ""

	@# --- Venv ---
	@echo "📦 Création du venv Python..."
	$(PYTHON) -m venv $(VENV)
	@echo "   ✅ Venv créé dans $(VENV)/"
	@echo ""

	@# --- Dépendances ---
	@echo "📥 Installation des dépendances..."
	$(VENV_PIP) install --upgrade pip --quiet
	$(VENV_PIP) install -r requirements.txt --quiet
	@echo "   ✅ Dépendances installées"
	@echo ""

	@# --- .env ---
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📋 Fichier .env créé depuis .env.example"; \
		API_KEY=$$($(VENV_PYTHON) -c "import secrets; print(secrets.token_hex(32))"); \
		sed -i.bak "s/^API_KEY=.*/API_KEY=$$API_KEY/" .env && rm -f .env.bak; \
		echo "   ✅ API_KEY générée automatiquement"; \
	else \
		echo "📋 Fichier .env déjà existant — non écrasé"; \
	fi
	@echo ""

	@# --- Git ---
	@if [ ! -d .git ]; then \
		git init; \
		git add .; \
		git commit -m "feat: initial project structure"; \
		echo "   ✅ Dépôt Git initialisé"; \
	else \
		echo "📁 Dépôt Git déjà existant — non réinitialisé"; \
	fi
	@echo ""

	@echo "============================================"
	@echo "✅ Projet initialisé avec succès !"
	@echo ""
	@echo "👉 Prochaines étapes :"
	@echo "   1. Activer le venv :"
	@echo "      source $(VENV_ACTIVATE)"
	@echo "   2. Vérifier le .env :"
	@echo "      cat .env"
	@echo "   3. Lancer les tests :"
	@echo "      make test"
	@echo "   4. Démarrer la stack :"
	@echo "      make up"
	@echo "============================================"

# =============================================================================
# STACK DOCKER
# =============================================================================

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

# =============================================================================
# QUALITÉ DU CODE
# =============================================================================

## Lance les tests avec coverage
test:
	$(PYTEST)

## Lance le linter flake8
lint:
	flake8 api/ dashboard/ tests/ --max-line-length=88

## Lance lint + tests
check: lint test

# =============================================================================
# DÉVELOPPEMENT LOCAL (sans Docker)
# =============================================================================

## Lance l'API et le dashboard sans Docker
dev:
	@echo "🔧 Démarrage en mode développement..."
	@echo "   API       → http://localhost:8000/docs"
	@echo "   Dashboard → http://localhost:8501"
	@trap 'kill %1 %2' INT; \
	$(VENV_PYTHON) -m uvicorn api.main:app \
	    --host 0.0.0.0 --port 8000 --reload & \
	$(VENV_PYTHON) -m streamlit run dashboard/app.py \
	    --server.port=8501 \
	    --server.address=localhost \
	    --browser.gatherUsageStats=false & \
	wait

## Lance uniquement l'API
dev-api:
	$(VENV_PYTHON) -m uvicorn api.main:app \
	    --host 0.0.0.0 --port 8000 --reload

## Lance uniquement le dashboard
run-dashboard:
	$(VENV_PYTHON) -m streamlit run dashboard/app.py \
		--server.address localhost \
		--server.port 8501

# =============================================================================
# NETTOYAGE
# =============================================================================

kill-ports: ## 🔪 Trouve et libère les ports 8000 et 8501
	@echo "🔍 Recherche des processus sur les ports 8000 et 8501..."
	@for port in 8000 8501; do \
		pid=$$(lsof -t -i:$$port 2>/dev/null); \
		if [ -n "$$pid" ]; then \
			echo "   ⚠️  Port $$port occupé par PID $$pid → kill..."; \
			kill -9 $$pid && echo "   ✅ Port $$port libéré"; \
		else \
			echo "   ℹ️  Port $$port déjà libre"; \
		fi \
	done
	@echo "✅ Ports libérés. Lance 'make dev' pour redémarrer."

## Supprime les fichiers de cache Python et de tests
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/
	@echo "✅ Cache nettoyé"

## Supprime tout (venv inclus) — repart de zéro
clean-all: clean down
	rm -rf $(VENV)
	@echo "✅ Venv supprimé — relancer 'make init' pour tout recréer"

# =============================================================================
# AIDE
# =============================================================================

## Affiche cette aide
help:
	@echo ""
	@echo "DevOps Monitor — Commandes disponibles"
	@echo "======================================="
	@grep -E '^## ' $(MAKEFILE_LIST) | \
	    sed 's/## /  /' | \
	    awk 'BEGIN {FS="\n"} {print}'
	@echo ""
