"""Pruebas de componente de la configuración leída del entorno."""

import pytest

from app.config import Configuracion, cargar_configuracion

pytestmark = pytest.mark.componente

VARIABLES = (
    "ADMIN_TOKEN",
    "PERMITIR_SABOTAJE",
    "MAX_PARTIDAS",
    "PARTIDA_TTL_MINUTOS",
    "RENDER_GIT_COMMIT",
    "APP_COMMIT",
)


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)


def test_valores_por_defecto():
    config = cargar_configuracion()

    assert config == Configuracion(
        admin_token="", permitir_sabotaje=True, max_partidas=500, partida_ttl_minutos=30
    )


def test_admin_token_vacio_por_defecto_bloquea_el_panel():
    assert cargar_configuracion().admin_token == ""


def test_lee_los_valores_del_entorno(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "  secreto  ")
    monkeypatch.setenv("PERMITIR_SABOTAJE", "false")
    monkeypatch.setenv("MAX_PARTIDAS", "3")
    monkeypatch.setenv("PARTIDA_TTL_MINUTOS", "5")

    config = cargar_configuracion()

    assert config.admin_token == "secreto"  # noqa: S105 - valor de prueba, no es una credencial (DEF-004)
    assert config.permitir_sabotaje is False
    assert config.max_partidas == 3
    assert config.partida_ttl_minutos == 5


def test_max_partidas_no_numerico_da_error_claro(monkeypatch):
    monkeypatch.setenv("MAX_PARTIDAS", "muchas")

    with pytest.raises(ValueError, match="MAX_PARTIDAS debe ser un número entero"):
        cargar_configuracion()


@pytest.mark.parametrize("valor", ["0", "-1"])
def test_ttl_debe_ser_mayor_que_cero(monkeypatch, valor):
    monkeypatch.setenv("PARTIDA_TTL_MINUTOS", valor)

    with pytest.raises(ValueError, match="PARTIDA_TTL_MINUTOS debe ser mayor que cero"):
        cargar_configuracion()


def test_permitir_sabotaje_invalido_da_error(monkeypatch):
    monkeypatch.setenv("PERMITIR_SABOTAJE", "quizas")

    with pytest.raises(ValueError, match="PERMITIR_SABOTAJE debe ser true o false"):
        cargar_configuracion()


def test_commit_por_defecto_es_local():
    assert cargar_configuracion().commit == "local"


def test_commit_se_lee_de_render(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "  abc123  ")

    assert cargar_configuracion().commit == "abc123"


def test_commit_usa_app_commit_fuera_de_render(monkeypatch):
    monkeypatch.setenv("APP_COMMIT", "def456")

    assert cargar_configuracion().commit == "def456"


def test_commit_de_render_tiene_prioridad(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc123")
    monkeypatch.setenv("APP_COMMIT", "def456")

    assert cargar_configuracion().commit == "abc123"


def test_commit_vacio_se_ignora(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "   ")
    monkeypatch.setenv("APP_COMMIT", "def456")

    assert cargar_configuracion().commit == "def456"
