"""Pruebas de componente del análisis de resultados de Locust (escalones, degradación y quiebre)."""

import pytest

from performance.analizar_resultados import Escalon, agrupar_escalones, puntos_criticos, reporte

pytestmark = [pytest.mark.componente, pytest.mark.no_funcional]


def fila(usuarios, p95, total, fallos, rps="10"):
    return {
        "User Count": str(usuarios),
        "95%": str(p95),
        "Requests/s": rps,
        "Total Request Count": str(total),
        "Total Failure Count": str(fallos),
    }


def test_agrupa_por_usuarios_y_calcula_fallos_del_escalon():
    filas = [
        fila(10, 20, 100, 0),
        fila(10, 30, 200, 0),
        fila(20, 600, 300, 2),  # escalón 2: 100 peticiones nuevas, 2 fallos nuevos
        fila(20, "N/A", 400, 6),  # sin dato de p95 en esta ventana
    ]

    escalones = agrupar_escalones(filas)

    assert escalones == [
        Escalon(usuarios=10, peticiones=200, fallos_pct=0.0, p95_ms=30.0, rps=10.0),
        Escalon(usuarios=20, peticiones=200, fallos_pct=3.0, p95_ms=600.0, rps=10.0),
    ]


def test_degradacion_y_quiebre():
    escalones = [
        Escalon(25, 100, 0.0, 120.0, 20.0),
        Escalon(50, 100, 0.5, 520.0, 30.0),  # incumple RNF-01: degradación
        Escalon(75, 100, 6.0, 900.0, 25.0),  # más del 5 % de fallos: quiebre
    ]

    degradacion, quiebre = puntos_criticos(escalones)

    assert degradacion.usuarios == 50
    assert quiebre.usuarios == 75


def test_sin_quiebre_lo_dice_en_el_reporte():
    escalones = [Escalon(25, 100, 0.0, 50.0, 20.0)]

    texto = reporte("local", escalones)

    assert puntos_criticos(escalones) == (None, None)
    assert "no se alcanzó hasta 25 usuarios" in texto
    assert "| 25 | 100 | 50 | 0.00 | 20.0 | OK |" in texto
