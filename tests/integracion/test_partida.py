"""Pruebas de integración de componentes: Partida + Puntaje + Ranking."""

import pytest

from app.dominio.errores import ErrorPartida
from app.dominio.modelos import EstadoPartida
from app.dominio.partida import Partida

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


# --- Respuestas inválidas -----------------------------------------------------------------------


def test_no_se_puede_responder_dos_veces(partida_con_jugadores):
    partida = partida_con_jugadores
    partida.iniciar()
    partida.responder("Ana", 0)

    with pytest.raises(ErrorPartida, match="ya respondió"):
        partida.responder("Ana", 1)
    assert partida.jugadores["Ana"].puntos == partida.puntos_ronda["Ana"]


def test_no_se_puede_responder_en_lobby(partida_con_jugadores):
    with pytest.raises(ErrorPartida, match="pregunta abierta"):
        partida_con_jugadores.responder("Ana", 0)


def test_no_se_puede_responder_en_resultados(partida_con_jugadores):
    partida = partida_con_jugadores
    partida.iniciar()
    partida.siguiente()

    with pytest.raises(ErrorPartida, match="pregunta abierta"):
        partida.responder("Ana", 0)


def test_jugador_desconocido_no_puede_responder(partida_con_jugadores):
    partida_con_jugadores.iniciar()

    with pytest.raises(ErrorPartida, match="no está en la partida"):
        partida_con_jugadores.responder("Intruso", 0)


@pytest.mark.parametrize("opcion", [-1, 4])
def test_opcion_fuera_de_rango(partida_con_jugadores, opcion):
    partida_con_jugadores.iniciar()

    with pytest.raises(ErrorPartida, match="entre 0 y 3"):
        partida_con_jugadores.responder("Ana", opcion)


def test_no_se_puede_iniciar_sin_jugadores(partida):
    with pytest.raises(ErrorPartida, match="al menos un jugador"):
        partida.iniciar()


def test_no_se_puede_iniciar_dos_veces(partida_con_jugadores):
    partida_con_jugadores.iniciar()

    with pytest.raises(ErrorPartida, match="ya fue iniciada"):
        partida_con_jugadores.iniciar()


def test_no_se_puede_avanzar_una_partida_finalizada(partida_con_jugadores):
    partida = partida_con_jugadores
    partida.iniciar()
    while partida.estado != EstadoPartida.FINALIZADA:
        partida.siguiente()

    with pytest.raises(ErrorPartida, match="No se puede avanzar"):
        partida.siguiente()


# --- Unirse ------------------------------------------------------------------------------------


@pytest.mark.parametrize("nombre", ["", "   ", "x" * 21])
def test_nombre_invalido(partida, nombre):
    with pytest.raises(ErrorPartida, match="entre 1 y 20"):
        partida.unirse(nombre)


@pytest.mark.parametrize("nombre", ["x", "x" * 20])
def test_nombre_en_los_limites_es_valido(partida, nombre):
    assert partida.unirse(nombre).nombre == nombre


def test_nombre_repetido_sin_distinguir_mayusculas(partida):
    partida.unirse("Ana")

    with pytest.raises(ErrorPartida, match="Ya hay un jugador"):
        partida.unirse("  ana ")


def test_no_se_puede_unir_con_la_partida_iniciada(partida_con_jugadores):
    partida_con_jugadores.iniciar()

    with pytest.raises(ErrorPartida, match="ya comenzó"):
        partida_con_jugadores.unirse("Tarde")


def test_limite_de_jugadores(reloj, preguntas):
    partida = Partida(pin="000001", preguntas=preguntas, reloj=reloj, max_jugadores=2)
    partida.unirse("Ana")
    partida.unirse("Beto")

    with pytest.raises(ErrorPartida, match="llena"):
        partida.unirse("Caro")


def test_partida_sin_preguntas_no_se_crea(reloj):
    with pytest.raises(ValueError, match="al menos una pregunta"):
        Partida(pin="000002", preguntas=[], reloj=reloj)
