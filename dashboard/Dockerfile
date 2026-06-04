# =============================================================================
# Stage unique — Dashboard Streamlit
# =============================================================================
FROM python:3.11-slim

LABEL maintainer="DevOps Monitor" \
	version="1.0.0" \
	description="Streamlit dashboard for DevOps Monitoring"

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --upgrade pip \
	&& pip install --no-cache-dir \
	streamlit==1.35.0 \
	httpx==0.27.0 \
	pandas==2.2.2

# Copier le code du dashboard
COPY dashboard/ ./dashboard/

# Créer un utilisateur non-root
RUN adduser --disabled-password --gecos "" appuser \
	&& chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
	CMD python -c "import httpx; httpx.get('http://localhost:8501/_stcore/health').raise_for_status()"

CMD ["streamlit", "run", "dashboard/app.py", \
	"--server.port=8501", \
	"--server.address=0.0.0.0", \
	"--server.headless=true", \
	"--browser.gatherUsageStats=false"]
