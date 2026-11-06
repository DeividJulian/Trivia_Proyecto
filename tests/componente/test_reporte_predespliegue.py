"""Pruebas de componente para el evaluador del reporte predespliegue."""

import json

import pytest

from scripts.reporte_predespliegue import (
    comprobar_job,
    construir_reporte,
    defectos_abiertos_altos,
    leer_cobertura,
    leer_junit,
    leer_mutantes,
    leer_rendimiento,
    leer_sonar,
    leer_trivy,
)

pytestmark = pytest.mark.componente


def test_junit_aprueba_sin_fallos(tmp_path):
    ruta = tmp_path / "suite.xml"
    ruta.write_text('<testsuite tests="1"><testcase name="ok" /></testsuite>', encoding="utf-8")

    resultado = leer_junit(ruta, "Sistema")

    assert resultado.estado == "APROBADA"
    assert "1 pruebas" in resultado.evidencia


def test_junit_falla_si_hay_un_error(tmp_path):
    ruta = tmp_path / "suite.xml"
    ruta.write_text(
        '<testsuite tests="1"><testcase name="mal"><failure /></testcase></testsuite>',
        encoding="utf-8",
    )

    assert leer_junit(ruta, "Sistema").estado == "FALLIDA"


def test_junit_reporta_pruebas_omitidas(tmp_path):
    ruta = tmp_path / "suite.xml"
    ruta.write_text(
        '<testsuite tests="1"><testcase name="omitida"><skipped /></testcase></testsuite>',
        encoding="utf-8",
    )

    resultado = leer_junit(ruta, "Humo")

    assert resultado.estado == "APROBADA"
    assert "1 omitidas" in resultado.evidencia


def test_cobertura_compara_con_el_minimo(tmp_path):
    ruta = tmp_path / "coverage.xml"
    ruta.write_text('<coverage line-rate="0.85" />', encoding="utf-8")

    assert leer_cobertura(ruta).estado == "APROBADA"


def test_mutantes_exige_seis_de_seis(tmp_path):
    ruta = tmp_path / "mutantes.txt"
    ruta.write_text("Mutantes detectados: 6/6 (100 %)", encoding="utf-8")

    assert leer_mutantes(ruta).estado == "APROBADA"


def test_trivy_bloquea_vulnerabilidades_criticas(tmp_path):
    ruta = tmp_path / "trivy.json"
    ruta.write_text(
        json.dumps(
            {"Results": [{"Vulnerabilities": [{"Severity": "CRITICAL", "VulnerabilityID": "CVE-1"}]}]}
        ),
        encoding="utf-8",
    )

    assert leer_trivy([ruta]).estado == "FALLIDA"


def test_sonar_diferido_no_se_considera_aprobado(tmp_path):
    resultado = leer_sonar(tmp_path / "quality-gate.json", "pending")

    assert resultado.estado == "PENDIENTE"
    assert comprobar_job("Estilo", "success").aprobada


def test_sonar_aprueba_solo_con_quality_gate_pasado(tmp_path):
    ruta = tmp_path / "quality-gate.json"
    ruta.write_text(json.dumps({"quality_gate": "PASSED"}), encoding="utf-8")

    assert leer_sonar(ruta, "success").estado == "APROBADA"


@pytest.mark.parametrize(("p95", "estado"), [(499, "APROBADA"), (500, "FALLIDA")])
def test_rendimiento_aplica_el_limite_p95(tmp_path, p95, estado):
    ruta = tmp_path / "stats.csv"
    ruta.write_text(
        "\n".join(
            [
                "Name,Request Count,Failure Count,95%,Median Response Time,Requests/s",
                f"Aggregated,100,0,{p95},10,12",
            ]
        ),
        encoding="utf-8",
    )

    assert leer_rendimiento(ruta).estado == estado


def test_reporte_no_aprueba_si_una_compuerta_esta_pendiente(tmp_path):
    reporte = construir_reporte([leer_sonar(tmp_path / "inexistente.json", "pending")])

    assert "NO DESPLEGAR" in reporte
    assert "PENDIENTE" in reporte


def test_no_hay_defectos_altos_abiertos_en_el_inventario_actual():
    from scripts.reporte_predespliegue import RAIZ

    assert defectos_abiertos_altos(RAIZ / "docs" / "REPORTE_DEFECTOS.md").aprobada


def test_defecto_alto_abierto_bloquea_el_reporte(tmp_path):
    ruta = tmp_path / "defectos.md"
    ruta.write_text(
        "\n".join(["### DEF-999 – Prueba", "| Severidad | Alta |", "| Estado | **Abierto** |"]),
        encoding="utf-8",
    )

    assert not defectos_abiertos_altos(ruta).aprobada
