"""Pruebas de componente del bono por velocidad (SOLICITUD_CAMBIO_001).

Se escribieron ANTES de implementar el cambio (primero la prueba).
"""

import pytest

from app.dominio import puntaje

LIMITE = 20.0

pytestmark = [pytest.mark.componente, pytest.mark.puntaje]


@pytest.mark.parametrize(
    ("tiempo", "bono"),
    [(0.0, 500), (5.0, 375), (10.0, 250), (15.0, 125), (20.0, 0)],
)
def test_bono_proporcional_al_tiempo_restante(tiempo, bono):
    assert puntaje.calcular_bono_velocidad(tiempo, LIMITE) == bono


def test_a_mitad_de_tiempo_el_bono_es_250():
    assert puntaje.calcular_bono_velocidad(10.0, 20.0) == 250


def test_tarde_no_hay_bono():
    assert puntaje.calcular_bono_velocidad(25.0, LIMITE) == 0


def test_respuesta_correcta_inmediata_suma_base_mas_500():
    assert puntaje.calcular_bono_velocidad(0.0, LIMITE) == puntaje.BONO_VELOCIDAD_MAX == 500
    assert puntaje.calcular_puntos(True, 0.0, LIMITE, racha=0) == (1500, 1)


def test_respuesta_correcta_a_mitad_de_tiempo_con_racha():
    assert puntaje.calcular_bono_velocidad(10.0, LIMITE) == 250
    assert puntaje.calcular_puntos(True, 10.0, LIMITE, racha=1) == (1000 + 250 + 100, 2)
