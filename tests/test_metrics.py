"""
Tests unitaires pour le module de métriques système.
"""
import pytest
from api.metrics import get_system_metrics


def test_metrics_returns_dict():
    """get_system_metrics() doit retourner un dictionnaire."""
    result = get_system_metrics()
    assert isinstance(result, dict)


def test_metrics_required_fields():
    """Les champs obligatoires doivent être présents."""
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
    """Les valeurs de mémoire en GB doivent être positives."""
    result = get_system_metrics()
    assert result["memory_total_gb"] > 0
    assert result["memory_used_gb"] >= 0
    assert result["memory_used_gb"] <= result["memory_total_gb"]


def test_disk_gb_positive():
    """Les valeurs de disque en GB doivent être positives."""
    result = get_system_metrics()
    assert result["disk_total_gb"] > 0
    assert result["disk_used_gb"] >= 0
    assert result["disk_used_gb"] <= result["disk_total_gb"]


def test_metrics_values_are_numbers():
    """Toutes les valeurs doivent être des nombres."""
    result = get_system_metrics()
    for key, value in result.items():
        assert isinstance(value, (int, float)), (
            f"{key} n'est pas un nombre : {type(value)}"
        )
