"""
Dashboard Streamlit — DevOps Monitoring Dashboard.

Onglets :
    - Métriques : KPIs temps réel + graphique sur 60 secondes
    - Serveurs  : tableau coloré + formulaire d'enregistrement
"""
import os
import time
from collections import deque
from datetime import datetime

import httpx
import pandas as pd
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")
HISTORY_SIZE = 60  # secondes de données conservées

st.set_page_config(
    page_title="DevOps Monitor",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helpers HTTP
# ---------------------------------------------------------------------------


def get_headers() -> dict:
    """Retourne les headers avec l'API Key."""
    return {"X-API-Key": API_KEY}


@st.cache_data(ttl=1)
def fetch_metrics() -> dict | None:
    """
    Récupère les métriques depuis l'API.

    Returns:
        dict ou None en cas d'erreur.
    """
    try:
        r = httpx.get(f"{API_BASE_URL}/metrics", timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def fetch_servers() -> list:
    """
    Récupère la liste des serveurs depuis l'API.

    Returns:
        list: Liste des serveurs ou liste vide en cas d'erreur.
    """
    try:
        r = httpx.get(f"{API_BASE_URL}/servers", timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def register_server(name: str, host: str, port: int) -> dict | None:
    """
    Enregistre un nouveau serveur via l'API.

    Args:
        name: Nom du serveur.
        host: Adresse IP ou hostname.
        port: Port du serveur.

    Returns:
        dict: Serveur créé ou None en cas d'erreur.
    """
    try:
        r = httpx.post(
            f"{API_BASE_URL}/servers",
            json={"name": name, "host": host, "port": port},
            headers=get_headers(),
            timeout=5,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")
        return None


def delete_server(server_id: str) -> bool:
    """
    Supprime un serveur via l'API.

    Args:
        server_id: ID du serveur à supprimer.

    Returns:
        bool: True si supprimé avec succès.
    """
    try:
        r = httpx.delete(
            f"{API_BASE_URL}/servers/{server_id}",
            headers=get_headers(),
            timeout=5,
        )
        return r.status_code == 204
    except Exception:
        return False


def trigger_check(server_id: str) -> dict | None:
    """
    Déclenche un health check manuel via l'API.

    Args:
        server_id: ID du serveur.

    Returns:
        dict: Serveur avec statut mis à jour ou None.
    """
    try:
        r = httpx.post(
            f"{API_BASE_URL}/servers/{server_id}/check",
            headers=get_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Initialisation du session_state
# ---------------------------------------------------------------------------

if "cpu_history" not in st.session_state:
    st.session_state.cpu_history = deque(maxlen=HISTORY_SIZE)
if "mem_history" not in st.session_state:
    st.session_state.mem_history = deque(maxlen=HISTORY_SIZE)
if "disk_history" not in st.session_state:
    st.session_state.disk_history = deque(maxlen=HISTORY_SIZE)
if "time_history" not in st.session_state:
    st.session_state.time_history = deque(maxlen=HISTORY_SIZE)

# ---------------------------------------------------------------------------
# Layout principal
# ---------------------------------------------------------------------------

st.title("📊 DevOps Monitoring Dashboard")
st.caption(f"API : `{API_BASE_URL}` · Actualisation automatique toutes les secondes")

tab_metrics, tab_servers = st.tabs(["📈 Métriques", "🖥️ Serveurs"])

# ===========================================================================
# Onglet Métriques
# ===========================================================================

with tab_metrics:
    st.subheader("Métriques système en temps réel")

    metrics = fetch_metrics()

    if metrics is None:
        st.error("⚠️ Impossible de joindre l'API. Vérifiez que le service est démarré.")
    else:
        # --- KPIs ---
        col1, col2, col3 = st.columns(3)

        cpu = metrics.get("cpu_percent", 0)
        mem = metrics.get("memory_percent", 0)
        disk = metrics.get("disk_percent", 0)

        col1.metric(
            label="🖥️ CPU",
            value=f"{cpu:.1f} %",
            delta=None,
            help="Utilisation CPU instantanée",
        )
        col2.metric(
            label="🧠 Mémoire",
            value=f"{mem:.1f} %",
            delta=None,
            help=(
                f"{metrics.get('memory_used_gb', 0):.1f} GB / "
                f"{metrics.get('memory_total_gb', 0):.1f} GB"
            ),
        )
        col3.metric(
            label="💾 Disque",
            value=f"{disk:.1f} %",
            delta=None,
            help=(
                f"{metrics.get('disk_used_gb', 0):.1f} GB / "
                f"{metrics.get('disk_total_gb', 0):.1f} GB"
            ),
        )

        # --- Historique ---
        now = datetime.now().strftime("%H:%M:%S")
        st.session_state.cpu_history.append(cpu)
        st.session_state.mem_history.append(mem)
        st.session_state.disk_history.append(disk)
        st.session_state.time_history.append(now)

        # --- Graphique ---
        if len(st.session_state.cpu_history) > 1:
            df_chart = pd.DataFrame(
                {
                    "CPU %": list(st.session_state.cpu_history),
                    "Mémoire %": list(st.session_state.mem_history),
                    "Disque %": list(st.session_state.disk_history),
                },
                index=list(st.session_state.time_history),
            )
            st.line_chart(df_chart, height=300)

        # Détails supplémentaires
        with st.expander("Détails mémoire & disque"):
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                st.write("**Mémoire**")
                st.write(
                    f"- Utilisée : {metrics.get('memory_used_gb', 0):.2f} GB"
                )
                st.write(
                    f"- Totale   : {metrics.get('memory_total_gb', 0):.2f} GB"
                )
            with dcol2:
                st.write("**Disque**")
                st.write(
                    f"- Utilisé : {metrics.get('disk_used_gb', 0):.2f} GB"
                )
                st.write(
                    f"- Total   : {metrics.get('disk_total_gb', 0):.2f} GB"
                )

    # Auto-refresh toutes les secondes
    time.sleep(1)
    st.rerun()

# ===========================================================================
# Onglet Serveurs
# ===========================================================================

with tab_servers:
    st.subheader("Serveurs enregistrés")

    servers_list = fetch_servers()

    # --- Tableau coloré ---
    if servers_list:
        STATUS_COLORS = {
            "UP": "🟢",
            "DEGRADED": "🟡",
            "DOWN": "🔴",
            "UNKNOWN": "⚪",
        }

        df_servers = pd.DataFrame(
            [
                {
                    "Statut": STATUS_COLORS.get(s["status"], "⚪")
                    + " "
                    + s["status"],
                    "Nom": s["name"],
                    "Host": s["host"],
                    "Port": s["port"],
                    "URL": s.get("base_url", ""),
                    "ID": s["id"],
                }
                for s in servers_list
            ]
        )

        st.dataframe(
            df_servers.drop(columns=["ID"]),
            use_container_width=True,
            hide_index=True,
        )

        # --- Actions sur serveurs ---
        st.markdown("#### Actions")
        action_col1, action_col2 = st.columns(2)

        with action_col1:
            server_names = {
                s["name"]: s["id"] for s in servers_list
            }
            selected_name = st.selectbox(
                "Sélectionner un serveur",
                options=list(server_names.keys()),
                key="select_server",
            )

        with action_col2:
            st.write("")
            st.write("")
            btn_col1, btn_col2 = st.columns(2)
            if selected_name:
                sid = server_names[selected_name]
                if btn_col1.button("🔍 Health Check"):
                    result = trigger_check(sid)
                    if result:
                        st.success(
                            f"Statut mis à jour : {result['status']}"
                        )
                    else:
                        st.error("Échec du health check")
                if btn_col2.button("🗑️ Supprimer"):
                    if delete_server(sid):
                        st.success(f"Serveur '{selected_name}' supprimé")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la suppression")
    else:
        st.info("Aucun serveur enregistré pour le moment.")

    st.markdown("---")

    # --- Formulaire d'enregistrement ---
    st.markdown("#### ➕ Enregistrer un nouveau serveur")

    with st.form("register_server_form", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns([2, 2, 1])
        with f_col1:
            f_name = st.text_input(
                "Nom du serveur", placeholder="prod-api-01"
            )
        with f_col2:
            f_host = st.text_input(
                "Host / IP", placeholder="192.168.1.100"
            )
        with f_col3:
            f_port = st.number_input(
                "Port", min_value=1, max_value=65535, value=8000
            )

        submitted = st.form_submit_button(
            "Enregistrer", use_container_width=True
        )

        if submitted:
            if not f_name or not f_host:
                st.error("Le nom et l'host sont obligatoires.")
            else:
                result = register_server(f_name, f_host, int(f_port))
                if result:
                    st.success(
                        f"✅ Serveur '{result['name']}' enregistré "
                        f"(ID: {result['id'][:8]}...)"
                    )
                    st.rerun()
