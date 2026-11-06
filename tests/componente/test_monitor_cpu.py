"""Pruebas de componente de las funciones puras del monitor de CPU de las pruebas de carga."""

import pytest

from performance.monitor_cpu import (
    UMBRAL_SATURACION_PCT,
    cpu_por_escalon,
    es_proceso,
    leer_muestras,
    porcentaje_docker,
    usuarios_en,
)

pytestmark = [pytest.mark.componente, pytest.mark.no_funcional]

HISTORIAL = [(100.0, 50), (120.0, 100), (140.0, 150)]


@pytest.mark.parametrize(
    ("texto", "esperado"), [("123.45%", 123.45), (" 0.50%\n", 0.5), ("--", None), ("", None)]
)
def test_porcentaje_docker(texto, esperado):
    assert porcentaje_docker(texto) == esperado


@pytest.mark.parametrize(
    ("cmdline", "esperado"),
    [
        (["C:\\proyecto\\.venv\\Scripts\\locust.exe", "-f", "x.py"], True),
        (["python", "-m", "LOCUST"], True),
        (["python", "app.py"], False),
        ([], False),
    ],
)
def test_es_proceso(cmdline, esperado):
    assert es_proceso(cmdline, "locust") is esperado


@pytest.mark.parametrize(
    ("momento", "usuarios"), [(99.0, 0), (100.0, 50), (119.9, 50), (120.0, 100), (500.0, 150)]
)
def test_usuarios_en_un_instante(momento, usuarios):
    assert usuarios_en(momento, HISTORIAL) == usuarios


def test_usuarios_en_sin_historial_es_cero():
    assert usuarios_en(10.0, []) == 0


def test_cpu_por_escalon_marca_la_saturacion_en_el_limite():
    muestras = [
        {"t": 101.0, "generador": 40.0, "servidor": 30.0, "sistema": 20.0},
        {"t": 110.0, "generador": 60.0, "servidor": 35.0, "sistema": 25.0},
        {"t": 125.0, "generador": UMBRAL_SATURACION_PCT, "servidor": -1.0, "sistema": 50.0},
        {"t": 90.0, "generador": 99.0, "servidor": 99.0, "sistema": 99.0},  # antes del inicio: se ignora
    ]

    escalones = cpu_por_escalon(muestras, HISTORIAL)

    assert set(escalones) == {50, 100}
    assert escalones[50] == {
        "generador_max": 60.0,
        "generador_media": 50.0,
        "servidor_max": 35.0,
        "saturado": False,
    }
    assert escalones[100]["saturado"] is True
    assert escalones[100]["servidor_max"] == -1.0  # docker no respondió


def test_leer_muestras(tmp_path):
    ruta = tmp_path / "cpu.csv"
    ruta.write_text("t,generador,servidor,sistema\n100.0,12.5,30.0,40.0\n", encoding="utf-8")

    assert leer_muestras(ruta) == [{"t": 100.0, "generador": 12.5, "servidor": 30.0, "sistema": 40.0}]


def test_cpu_del_contenedor_no_se_cuelga_si_docker_no_responde(monkeypatch):
    """DEF-036: docker stats sin respuesta -> -1 (sin dato), y el monitor sigue."""
    import subprocess

    from performance import monitor_cpu

    llamadas = {}

    def docker_colgado(*args, **kwargs):
        llamadas["timeout"] = kwargs.get("timeout")
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout"))

    monkeypatch.setattr(monitor_cpu.shutil, "which", lambda _nombre: "docker")
    monkeypatch.setattr(monitor_cpu.subprocess, "run", docker_colgado)

    assert monitor_cpu._cpu_contenedor("testquiz-carga") == -1.0
    assert llamadas["timeout"] == monitor_cpu.TIMEOUT_DOCKER_S
