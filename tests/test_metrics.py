"""
Tests unitaires pour le module de métriques système.
"""
from unittest.mock import patch, MagicMock
from api.metrics import get_system_metrics


# ---------------------------------------------------------------------------
# Tests de base
# ---------------------------------------------------------------------------


def test_metrics_returns_dict():
    """get_system_metrics() doit retourner un dictionnaire."""
    result = get_system_metrics()
    assert isinstance(result, dict)


def test_metrics_required_fields():
    """Les 7 champs obligatoires doivent être présents."""
    result = get_system_metrics()
    required_fields = [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "memory_total_gb",
        "memory_used_gb",
        "disk_total_gb",
        "disk_used_gb",
    ]
    for field in required_fields:
        assert field in result, f"Champ manquant : {field}"


def test_metrics_values_are_numbers():
    """Toutes les valeurs doivent être des int ou float."""
    result = get_system_metrics()
    for key, value in result.items():
        assert isinstance(value, (int, float)), (
            f"{key} n'est pas un nombre : {type(value)}"
        )


# ---------------------------------------------------------------------------
# Tests de plages
# ---------------------------------------------------------------------------


def test_cpu_percent_range():
    """cpu_percent doit être entre 0 et 100."""
    result = get_system_metrics()
    assert 0 <= result["cpu_percent"] <= 100


def test_memory_percent_range():
    """memory_percent doit être entre 0 et 100."""
    result = get_system_metrics()
    assert 0 <= result["memory_percent"] <= 100


def test_disk_percent_range():
    """disk_percent doit être entre 0 et 100."""
    result = get_system_metrics()
    assert 0 <= result["disk_percent"] <= 100


def test_memory_gb_positive():
    """Les valeurs de mémoire en GB doivent être cohérentes."""
    result = get_system_metrics()
    assert result["memory_total_gb"] > 0
    assert result["memory_used_gb"] >= 0
    assert result["memory_used_gb"] <= result["memory_total_gb"]


def test_disk_gb_positive():
    """Les valeurs de disque en GB doivent être cohérentes."""
    result = get_system_metrics()
    assert result["disk_total_gb"] > 0
    assert result["disk_used_gb"] >= 0
    assert result["disk_used_gb"] <= result["disk_total_gb"]


# ---------------------------------------------------------------------------
# Tests avec mock psutil
# ---------------------------------------------------------------------------


def _make_mock_psutil(cpu=42.0, mem_percent=55.0, mem_total=8 * 1024**3,
                      mem_used=4 * 1024**3, disk_percent=70.0,
                      disk_total=500 * 1024**3, disk_used=350 * 1024**3):
    """Helper : retourne des mocks psutil configurables."""
    mock_mem = MagicMock()
    mock_mem.percent = mem_percent
    mock_mem.total = mem_total
    mock_mem.used = mem_used

    mock_disk = MagicMock()
    mock_disk.percent = disk_percent
    mock_disk.total = disk_total
    mock_disk.used = disk_used

    return cpu, mock_mem, mock_disk


def test_metrics_cpu_value_mocked():
    """Vérifie que cpu_percent reflète la valeur psutil."""
    cpu, mock_mem, mock_disk = _make_mock_psutil(cpu=75.5)
    with patch("api.metrics.psutil.cpu_percent", return_value=cpu), \
         patch("api.metrics.psutil.virtual_memory", return_value=mock_mem), \
         patch("api.metrics.psutil.disk_usage", return_value=mock_disk):
        result = get_system_metrics()
    assert result["cpu_percent"] == 75.5


def test_metrics_memory_values_mocked():
    """Vérifie le calcul mémoire en GB."""
    cpu, mock_mem, mock_disk = _make_mock_psutil(
        mem_percent=60.0,
        mem_total=16 * 1024**3,
        mem_used=8 * 1024**3,
    )
    with patch("api.metrics.psutil.cpu_percent", return_value=cpu), \
         patch("api.metrics.psutil.virtual_memory", return_value=mock_mem), \
         patch("api.metrics.psutil.disk_usage", return_value=mock_disk):
        result = get_system_metrics()
    assert result["memory_percent"] == 60.0
    assert result["memory_total_gb"] == 16.0
    assert result["memory_used_gb"] == 8.0


def test_metrics_disk_values_mocked():
    """Vérifie le calcul disque en GB."""
    cpu, mock_mem, mock_disk = _make_mock_psutil(
        disk_percent=80.0,
        disk_total=1000 * 1024**3,
        disk_used=800 * 1024**3,
    )
    with patch("api.metrics.psutil.cpu_percent", return_value=cpu), \
         patch("api.metrics.psutil.virtual_memory", return_value=mock_mem), \
         patch("api.metrics.psutil.disk_usage", return_value=mock_disk):
        result = get_system_metrics()
    assert result["disk_percent"] == 80.0
    assert result["disk_total_gb"] == 1000.0
    assert result["disk_used_gb"] == 800.0


def test_metrics_cpu_zero():
    """cpu_percent peut être 0 (machine idle)."""
    cpu, mock_mem, mock_disk = _make_mock_psutil(cpu=0.0)
    with patch("api.metrics.psutil.cpu_percent", return_value=cpu), \
         patch("api.metrics.psutil.virtual_memory", return_value=mock_mem), \
         patch("api.metrics.psutil.disk_usage", return_value=mock_disk):
        result = get_system_metrics()
    assert result["cpu_percent"] == 0.0


def test_metrics_rounding():
    """Les valeurs GB doivent être arrondies à 2 décimales."""
    cpu, mock_mem, mock_disk = _make_mock_psutil(
        mem_total=int(8.5 * 1024**3),
        mem_used=int(3.333 * 1024**3),
        disk_total=int(256.7 * 1024**3),
        disk_used=int(128.123 * 1024**3),
    )
    with patch("api.metrics.psutil.cpu_percent", return_value=cpu), \
         patch("api.metrics.psutil.virtual_memory", return_value=mock_mem), \
         patch("api.metrics.psutil.disk_usage", return_value=mock_disk):
        result = get_system_metrics()
    # Vérifie max 2 décimales
    for key in ["memory_total_gb", "memory_used_gb", "disk_total_gb", "disk_used_gb"]:
        val = result[key]
        assert round(val, 2) == val, f"{key} non arrondi : {val}"
