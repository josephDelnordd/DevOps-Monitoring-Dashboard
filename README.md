# 📊 DevOps Monitoring Dashboard

Système de monitoring temps réel construit en Python, containerisé avec Docker et déployé sur Azure Container Apps via un pipeline CI/CD GitHub Actions.

## Structure du projet

```
devops-monitor/
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── auth.py
│   ├── metrics.py
│   ├── poller.py
│   └── Dockerfile
├── dashboard/
│   ├── app.py
│   └── Dockerfile
├── tests/
│   ├── test_metrics.py
│   └── test_routes.py
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── .env.example
├── Makefile
├── requirements.txt
└── README.md
```

## Architecture

```
GitHub Actions CI/CD
├── lint (flake8)
├── test (pytest --cov ≥ 75%)
├── build & push → Azure Container Registry
└── deploy → Azure Container Apps

Azure Container Apps
├── devops-monitor-api   (FastAPI — port 8000)
└── devops-monitor-dashboard (Streamlit — port 8501)
```


## Prérequis

- Python 3.11+
- Docker & Docker Compose
- Make
- (Optionnel) Azure CLI pour le déploiement

## Lancement local en < 5 minutes

```bash
# 1. Cloner le dépôt
git clone https://github.com/<votre-username>/devops-monitor.git
cd devops-monitor

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et remplir API_KEY avec une valeur de votre choix

# 3. Démarrer la stack
make up

# 4. Accéder aux services
# API     → http://localhost:8000/docs
# Dashboard → http://localhost:8501
```

