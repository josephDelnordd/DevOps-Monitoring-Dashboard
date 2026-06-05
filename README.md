# 📊 DevOps Monitoring Dashboard

![CI/CD](https://github.com/josephDelnordd/DevOps-Monitoring-Dashboard/actions/workflows/ci-cd.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Azure](https://img.shields.io/badge/azure-deployed-0089D6.svg)

Système de monitoring temps réel construit en Python, containerisé avec Docker et déployé sur **Azure Web Apps** via un pipeline CI/CD GitHub Actions.

---

## 🌐 Démo en production

| Service | URL |
|---------|-----|
| 🖥️ Dashboard | [devops-monitor-dashboard.azurewebsites.net](https://devops-monitor-dashboard-fubmcjegh2bjcec3.swedencentral-01.azurewebsites.net) |
| ⚡ API | [devops-monitoring-api.azurewebsites.net](https://devops-monitoring-api-fabaa3cweffug8cj.swedencentral-01.azurewebsites.net/health) |

---

## 🏗️ Architecture

```bash
GitHub Push → main
│
├── 🧪 Lint & Test (flake8 + pytest --cov ≥ 75%)
│
├── 🐳 Build & Push → Docker Hub
│       ├── devops-monitor-api:latest
│       └── devops-monitor-dashboard:latest
│
└── 🚀 Deploy → Azure Web Apps (Sweden Central)
├── devops-monitoring-api      (FastAPI   — port 8000)
└── devops-monitor-dashboard   (Streamlit — port 8501)
```

---

### 📂 Structure du projet

```bash
devops-monitoring-dashboard/
├── Makefile
├── README.md
├── docker-compose.yml
├── pytest.ini
├── conftest.py
├── requirements.txt
├── api/
│   ├── Dockerfile
│   ├── main.py
│   ├── auth.py
│   ├── metrics.py
│   ├── models.py
│   └── poller.py
├── dashboard/
│   ├── Dockerfile
│   └── app.py
└── tests/
├── test_metrics.py
├── test_poller.py
└── test_routes.py
```

---


---

## ⚙️ Prérequis

- Python 3.11+
- Docker & Docker Compose
- Make
- *(Optionnel)* Azure CLI pour le déploiement

---

## 🚀 Lancement local

```bash
# 1. Cloner le dépôt
git clone https://github.com/josephDelnordd/DevOps-Monitoring-Dashboard.git
cd DevOps-Monitoring-Dashboard

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner API_KEY avec une valeur de votre choix

# 3. Démarrer la stack
make up

# 4. Accéder aux services
API       → http://localhost:8000/docs
Dashboard → http://localhost:8501
```

---

## 🧪 Tests

```bash
# Lancer les tests avec couverture
make test

# Lint
make lint
```

Couverture minimale requise : **75%**

---


## 🔐 Sécurité

| Mesure | Détail |
|--------|--------|
| Authentification | Header `X-API-Key` requis sur `/metrics` |
| Secrets | Gérés via GitHub Secrets + `.env` local |
| HTTPS | Activé par défaut sur Azure Web Apps |
| `.env` | Non commité (`.gitignore`) |

```bash
# Exemple d'appel authentifié
curl -H "X-API-Key: votre-clé" \
  https://devops-monitoring-api-fabaa3cweffug8cj.swedencentral-01.azurewebsites.net/metrics

# Sans clé → 403 Forbidden
```

---

## 🔧 Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `API_KEY` | Clé d'authentification API | `mon-secret-123` |
| `API_BASE_URL` | URL de l'API pour le dashboard | `http://localhost:8000` |

---

## 📦 GitHub Secrets requis (CI/CD)

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Nom d'utilisateur Docker Hub |
| `DOCKERHUB_TOKEN` | Token d'accès Docker Hub |
| `AZURE_WEBAPP_API_NAME` | Nom de la Web App API Azure |
| `AZURE_WEBAPP_DASHBOARD_NAME` | Nom de la Web App Dashboard Azure |
| `AZURE_WEBAPP_API_PUBLISH_PROFILE` | Profil de publication API |
| `AZURE_WEBAPP_DASHBOARD_PUBLISH_PROFILE` | Profil de publication Dashboard |

---

## 📋 Commandes Make disponibles


| Commande | Description |
|---------|-------------|
| `make init` | Initialiser le projet (venv + dépendances + .env) |
| `make up` | Démarrer les services Docker |
| `make down` | Arrêter les services |
| `make dev` | Lancer l'API + Dashboard sans Docker |
| `make dev-api` | Lancer uniquement l'API |
| `make dev-dashboard` | Lancer uniquement le Dashboard |
| `make test` | Lancer les tests avec coverage |
| `make lint` | Vérifier le style de code |
| `make check` | Lint + Tests |
| `make kill-ports` | Libérer les ports 8000 et 8501 |
| `make logs` | Afficher les logs Docker |
| `make clean` | Supprimer les fichiers de cache |
| `make clean-all` | Supprimer tout (venv inclus) |

---

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## Auteur

Joseph Delnord - [GitHub](https://github.com/josephDelnordd)