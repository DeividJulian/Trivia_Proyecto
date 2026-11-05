"""Pruebas de componente de las reglas de puntaje."""

import pytest

from app.dominio.puntaje import (
    BONO_RACHA_MAX,
    calcular_bono_racha,
    es_respuesta_a_tiempo,
    sumar_racha,
)

pytestmark = [pytest.mark.componente, pytest.mark.puntaje]

LIMITE = 20.0


# --- Valores límite de "a tiempo" -----------------------------------------------------------------


def test_respuesta_justo_en_el_limite_cuenta_a_tiempo():
    assert es_respuesta_a_tiempo(20.0, LIMITE) is True


def test_una_milesima_despues_del_limite_es_tarde():
    assert es_respuesta_a_tiempo(20.001, LIMITE) is False


def test_una_milesima_antes_del_limite_es_a_tiempo():
    assert es_respuesta_a_tiempo(19.999, LIMITE) is True


def test_respuesta_inmediata_es_a_tiempo():
    assert es_respuesta_a_tiempo(0.0, LIMITE) is True


# --- Racha ---------------------------------------------------------------------------------------


def test_acertar_suma_uno_a_la_racha():
    assert sumar_racha(2, acerto=True) == 3


def test_fallar_reinicia_la_racha():
    assert sumar_racha(4, acerto=False) == 0


@pytest.mark.parametrize(("racha", "bono"), [(0, 0), (1, 0), (2, 100), (3, 200), (6, 500)])
def test_la_racha_empieza_en_el_segundo_acierto(racha, bono):
    assert calcular_bono_racha(racha) == bono


@pytest.mark.parametrize("racha", [7, 10, 100])
def test_bono_de_racha_tiene_tope_500(racha):
    assert calcular_bono_racha(racha) == BONO_RACHA_MAX == 500
