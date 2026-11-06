"""Cada mutante cambia el comportamiento SOLO cuando está activo.

Estas pruebas comprueban que el mutante está bien conectado. Que las demás pruebas lo detecten
(lo "maten") lo verifica scripts/verificar_mutantes.py.
"""

import pytest

from app.dominio import sabotajes
from app.dominio.modelos import Jugador
from app.dominio.puntaje import calcular_puntos, es_respuesta_a_tiempo, sumar_racha
from app.dominio.ranking import ordenar_ranking

pytestmark = [pytest.mark.componente, pytest.mark.sabotajes]


@pytest.fixture
def sin_sabotajes():
    sabotajes.desactivar_todos()


def test_tiempo_estricto(sin_sabotajes):
    assert es_respuesta_a_tiempo(20.0, 20.0) is True

    sabotajes.activar("tiempo_estricto")

    assert es_respuesta_a_tiempo(20.0, 20.0) is False


def test_racha_no_suma(sin_sabotajes):
    assert sumar_racha(2, acerto=True) == 3

    sabotajes.activar("racha_no_suma")

    assert sumar_racha(2, acerto=True) == 2


def test_bono_sin_acierto(sin_sabotajes):
    assert calcular_puntos(False, 1.0, 20.0, racha=0) == (0, 0)

    sabotajes.activar("bono_sin_acierto")

    assert calcular_puntos(False, 1.0, 20.0, racha=0) == (475, 0)


def test_empates_mal(sin_sabotajes):
    jugadores = [Jugador("Ana", puntos=100, tiempo_total=9.0), Jugador("Beto", puntos=100, tiempo_total=1.0)]
    assert [f.nombre for f in ordenar_ranking(jugadores)] == ["Beto", "Ana"]

    sabotajes.activar("empates_mal")

    assert [f.nombre for f in ordenar_ranking(jugadores)] == ["Ana", "Beto"]


def test_no_guarda_respuesta(sin_sabotajes, partida_con_jugadores):
    sabotajes.activar("no_guarda_respuesta")
    partida_con_jugadores.iniciar()

    partida_con_jugadores.responder("Ana", 0)
    partida_con_jugadores.responder("Ana", 0)  # sin el mutante esto sería un error

    assert partida_con_jugadores.respuestas == {}
