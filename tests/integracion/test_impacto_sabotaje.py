"""Pruebas de integración del cálculo de impacto del sabotaje en Partida."""

import pytest

from app.dominio import sabotajes
from app.dominio.modelos import EstadoPartida, Pregunta
from app.dominio.partida import Partida

pytestmark = [pytest.mark.integracion, pytest.mark.partida, pytest.mark.sabotajes]


def test_impacto_racha_no_suma_tres_aciertos_en_el_limite(reloj):
    """Con racha_no_suma, 3 aciertos justo en el límite dan reales 3300, mostrados 3000, dif -300."""
    preguntas = [
        Pregunta(texto="P1", opciones=("A", "B", "C", "D"), correcta=0, tiempo_limite=20.0),
        Pregunta(texto="P2", opciones=("A", "B", "C", "D"), correcta=1, tiempo_limite=20.0),
        Pregunta(texto="P3", opciones=("A", "B", "C", "D"), correcta=2, tiempo_limite=20.0),
    ]
    partida = Partida(pin="111111", preguntas=preguntas, reloj=reloj)
    sabotajes.activar("racha_no_suma")
    partida.unirse("Ana")
    partida.iniciar()

    # Pregunta 1
    reloj.avanzar(20.0)
    partida.responder("Ana", 0)  # Se cierra sola al responder el único jugador
    assert partida.estado == EstadoPartida.RESULTADOS
    partida.siguiente()  # Pasa a Pregunta 2

    # Pregunta 2
    reloj.avanzar(20.0)
    partida.responder("Ana", 1)  # Se cierra sola
    assert partida.estado == EstadoPartida.RESULTADOS
    partida.siguiente()  # Pasa a Pregunta 3

    # Pregunta 3
    reloj.avanzar(20.0)
    partida.responder("Ana", 2)

    jugador = partida.buscar_jugador("Ana")
    assert jugador.puntos == 3000
    assert jugador.puntos_reales == 3300
    assert jugador.puntos - jugador.puntos_reales == -300

    impacto = partida.impacto_por_jugador()
    assert len(impacto) == 1
    assert impacto[0]["jugador"] == "Ana"
    assert impacto[0]["puntos_mostrados"] == 3000
    assert impacto[0]["puntos_reales"] == 3300
    assert impacto[0]["diferencia"] == -300
    assert impacto[0]["desglose"]["racha_no_suma"] == -300

    resumen = partida.resumen_por_sabotaje()
    assert resumen["racha_no_suma"]["puntos_de_diferencia"] == -300
    assert resumen["racha_no_suma"]["respuestas_afectadas"] == 2


def test_impacto_bono_sin_acierto_respuesta_incorrecta(partida, reloj):
    """Con bono_sin_acierto, respuesta incorrecta a 1 s de 20 da mostrados 475, reales 0, dif +475."""
    sabotajes.activar("bono_sin_acierto")
    partida.unirse("Beto")
    partida.iniciar()

    reloj.avanzar(1.0)
    # Correcta es 0, opción 3 es incorrecta
    puntos = partida.responder("Beto", 3)

    assert puntos == 475
    jugador = partida.buscar_jugador("Beto")
    assert jugador.puntos == 475
    assert jugador.puntos_reales == 0
    assert jugador.puntos - jugador.puntos_reales == 475

    assert len(partida.impacto) == 1
    assert partida.impacto[0].puntos_mostrados == 475
    assert partida.impacto[0].puntos_reales == 0
    assert partida.impacto[0].diferencia == 475
    assert "bono_sin_acierto" in partida.impacto[0].nota

    impacto = partida.impacto_por_jugador()
    assert impacto[0]["desglose"]["bono_sin_acierto"] == 475


def test_impacto_empates_mal_posicion_mostrada_distinta_de_la_real(partida, reloj):
    """Con empates_mal y dos jugadores empatados, la posición mostrada difiere de la real."""
    sabotajes.activar("empates_mal")
    partida.unirse("Beto")
    partida.unirse("Ana")
    partida.iniciar()

    # Beto responde mal a 1.0 s
    reloj.avanzar(1.0)
    partida.responder("Beto", 3)

    # Ana responde mal a 5.0 s
    reloj.avanzar(4.0)
    partida.responder("Ana", 3)

    # Ambos tienen 0 puntos, pero Beto tardó 1.0 s y Ana 5.0 s
    ranking_mostrado = partida.ranking()
    assert ranking_mostrado[0].nombre == "Ana"  # Alfabético por empates_mal
    assert ranking_mostrado[1].nombre == "Beto"

    ranking_real = partida.ranking_real()
    assert ranking_real[0].nombre == "Beto"  # Menor tiempo real
    assert ranking_real[1].nombre == "Ana"

    impacto = partida.impacto_por_jugador()
    impacto_dict = {item["jugador"]: item for item in impacto}
    assert impacto_dict["Ana"]["posicion_mostrada"] == 1
    assert impacto_dict["Ana"]["posicion_real"] == 2
    assert impacto_dict["Beto"]["posicion_mostrada"] == 2
    assert impacto_dict["Beto"]["posicion_real"] == 1


def test_impacto_no_guarda_respuesta_segunda_respuesta_reales_cero(partida, reloj):
    """Con no_guarda_respuesta, responder dos veces da reales 0 y nota de 409."""
    sabotajes.activar("no_guarda_respuesta")
    partida.unirse("Ana")
    partida.iniciar()

    reloj.avanzar(2.0)
    # Primera respuesta: correcta
    puntos_1 = partida.responder("Ana", 0)
    assert puntos_1 > 0
    assert partida.impacto[0].puntos_reales == puntos_1
    assert partida.impacto[0].diferencia == 0

    # Segunda respuesta a la misma pregunta
    reloj.avanzar(1.0)
    puntos_2 = partida.responder("Ana", 0)
    assert puntos_2 > 0
    assert partida.impacto[1].puntos_reales == 0
    assert partida.impacto[1].diferencia == puntos_2
    assert partida.impacto[1].nota == "respuesta repetida: sin el sabotaje habría sido rechazada (409)"

    jugador = partida.buscar_jugador("Ana")
    assert jugador.puntos == puntos_1 + puntos_2
    assert jugador.puntos_reales == puntos_1

    impacto = partida.impacto_por_jugador()
    assert impacto[0]["desglose"]["no_guarda_respuesta"] == puntos_2


def test_impacto_tiempo_estricto_en_el_limite(partida, reloj):
    """Con tiempo_estricto, respuesta justo en el límite da mostrados 0, reales 1000."""
    sabotajes.activar("tiempo_estricto")
    partida.unirse("Ana")
    partida.iniciar()

    reloj.avanzar(20.0)  # Justo en el límite
    puntos = partida.responder("Ana", 0)

    assert puntos == 0
    jugador = partida.buscar_jugador("Ana")
    assert jugador.puntos == 0
    assert jugador.puntos_reales == 1000
    assert jugador.puntos - jugador.puntos_reales == -1000

    assert len(partida.impacto) == 1
    assert partida.impacto[0].puntos_mostrados == 0
    assert partida.impacto[0].puntos_reales == 1000
    assert partida.impacto[0].diferencia == -1000
    assert partida.impacto[0].nota == "respuesta en el límite tomada como tardía (tiempo_estricto)"

    impacto = partida.impacto_por_jugador()
    assert impacto[0]["desglose"]["tiempo_estricto"] == -1000


@pytest.mark.xfail(strict=True, reason="DEF-033 abierto: el desglose usa la racha real ya actualizada")
def test_desglose_con_dos_sabotajes_atribuye_cada_diferencia_a_su_sabotaje(reloj):
    """DEF-033: con racha_no_suma y bono_sin_acierto a la vez, cada diferencia va a su sabotaje."""
    preguntas = [
        Pregunta(texto="P1", opciones=("A", "B", "C", "D"), correcta=0, tiempo_limite=20.0),
        Pregunta(texto="P2", opciones=("A", "B", "C", "D"), correcta=1, tiempo_limite=20.0),
    ]
    partida = Partida(pin="222222", preguntas=preguntas, reloj=reloj)
    sabotajes.activar("racha_no_suma")
    sabotajes.activar("bono_sin_acierto")
    partida.unirse("Ana")
    partida.unirse("Beto")
    partida.iniciar()

    for correcta in (0, 1):
        reloj.avanzar(1.0)
        partida.responder("Beto", 3)  # incorrecta y rápida: bono que no le corresponde
        reloj.avanzar(19.0)
        partida.responder("Ana", correcta)  # correcta justo en el límite: sin bono por velocidad
        partida.siguiente()

    resumen = partida.resumen_por_sabotaje()
    desglose = {fila["jugador"]: fila["desglose"] for fila in partida.impacto_por_jugador()}

    assert resumen["bono_sin_acierto"] == {"respuestas_afectadas": 2, "puntos_de_diferencia": 950}
    assert resumen["racha_no_suma"] == {"respuestas_afectadas": 1, "puntos_de_diferencia": -100}
    assert desglose["Ana"]["racha_no_suma"] == -100
    assert desglose["Ana"]["bono_sin_acierto"] == 0
    assert desglose["Beto"]["bono_sin_acierto"] == 950
