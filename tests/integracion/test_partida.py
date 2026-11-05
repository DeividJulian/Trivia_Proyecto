"""Pruebas de integración de componentes: Partida + Puntaje + Ranking."""

import pytest

from app.dominio.modelos import EstadoPartida

pytestmark = [pytest.mark.integracion, pytest.mark.partida]


def test_flujo_lobby_pregunta_resultados_finalizada(partida_con_jugadores, reloj):
    partida = partida_con_jugadores
    assert partida.estado == EstadoPartida.LOBBY

    partida.iniciar()
    assert partida.estado == EstadoPartida.PREGUNTA
    assert partida.estado_publico()["numero_pregunta"] == 1

    for _ in range(len(partida.preguntas)):
        reloj.avanzar(3)
        partida.siguiente()  # cierra la pregunta
        assert partida.estado == EstadoPartida.RESULTADOS
        partida.siguiente()  # pasa a la siguiente o termina

    assert partida.estado == EstadoPartida.FINALIZADA
    assert partida.estado_publico()["ganador"] is not None


def test_la_pregunta_se_cierra_sola_cuando_todos_responden(partida_con_jugadores):
    partida = partida_con_jugadores
    partida.iniciar()

    for nombre in ("Ana", "Beto", "Caro"):
        partida.responder(nombre, 0)

    assert partida.estado == EstadoPartida.RESULTADOS


def test_tiempo_restante_baja_con_el_reloj(partida_con_jugadores, reloj):
    partida = partida_con_jugadores
    partida.iniciar()

    reloj.avanzar(7.5)

    assert partida.tiempo_restante() == pytest.approx(12.5)
    reloj.avanzar(100)
    assert partida.tiempo_restante() == 0.0


def test_estado_publico_oculta_la_correcta_mientras_la_pregunta_esta_abierta(partida_con_jugadores):
    partida = partida_con_jugadores
    partida.iniciar()

    abierto = partida.estado_publico()
    assert "correcta" not in abierto
    assert "ranking" not in abierto
    assert abierto["pregunta"]["opciones"] == ["A", "B", "C", "D"]

    partida.siguiente()
    resultados = partida.estado_publico()
    assert resultados["correcta"] == 0
    assert len(resultados["ranking"]) == 3


def test_estado_publico_en_lobby_no_tiene_pregunta(partida_con_jugadores):
    estado = partida_con_jugadores.estado_publico()

    assert estado["estado"] == "LOBBY"
    assert estado["pregunta"] is None
    assert estado["jugadores"] == ["Ana", "Beto", "Caro"]
