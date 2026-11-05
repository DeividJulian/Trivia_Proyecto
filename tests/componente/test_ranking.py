"""Pruebas de componente del ranking y sus desempates."""

import pytest

from app.dominio.modelos import Jugador
from app.dominio.ranking import FilaRanking, obtener_ganador, ordenar_ranking

pytestmark = [pytest.mark.componente, pytest.mark.ranking]


def nombres(ranking: list[FilaRanking]) -> list[str]:
    return [fila.nombre for fila in ranking]


def test_mas_puntos_va_primero():
    jugadores = [Jugador("Ana", puntos=1000), Jugador("Beto", puntos=2500), Jugador("Caro", puntos=1500)]

    assert nombres(ordenar_ranking(jugadores)) == ["Beto", "Caro", "Ana"]


def test_empate_en_puntos_gana_el_de_menor_tiempo():
    jugadores = [
        Jugador("Ana", puntos=2000, tiempo_total=9.5),
        Jugador("Beto", puntos=2000, tiempo_total=4.2),
    ]

    assert nombres(ordenar_ranking(jugadores)) == ["Beto", "Ana"]


def test_empate_en_puntos_y_tiempo_desempata_por_nombre():
    jugadores = [
        Jugador("Carlos", puntos=2000, tiempo_total=5.0),
        Jugador("ana", puntos=2000, tiempo_total=5.0),
        Jugador("Beto", puntos=2000, tiempo_total=5.0),
    ]

    assert nombres(ordenar_ranking(jugadores)) == ["ana", "Beto", "Carlos"]


def test_los_puntos_pesan_mas_que_el_tiempo():
    jugadores = [
        Jugador("Lento", puntos=3000, tiempo_total=50.0),
        Jugador("Rapido", puntos=2000, tiempo_total=1.0),
    ]

    assert nombres(ordenar_ranking(jugadores)) == ["Lento", "Rapido"]


def test_posiciones_numeradas_desde_uno():
    ranking = ordenar_ranking([Jugador("Ana", puntos=10), Jugador("Beto", puntos=20)])

    assert [fila.posicion for fila in ranking] == [1, 2]
    assert ranking[0] == FilaRanking(posicion=1, nombre="Beto", puntos=20, tiempo_total=0.0)


def test_ranking_vacio():
    assert ordenar_ranking([]) == []


def test_sin_jugadores_no_hay_ganador():
    assert obtener_ganador([]) is None


def test_ganador_respeta_los_desempates():
    jugadores = [
        Jugador("Ana", puntos=2000, tiempo_total=8.0),
        Jugador("Beto", puntos=2000, tiempo_total=3.0),
    ]

    assert obtener_ganador(jugadores).nombre == "Beto"
