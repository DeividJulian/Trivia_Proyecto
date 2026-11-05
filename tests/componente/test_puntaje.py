"""Pruebas de componente de las reglas de puntaje."""

import pytest

from app.dominio.puntaje import es_respuesta_a_tiempo

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
