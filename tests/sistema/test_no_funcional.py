"""Pruebas de sistema NO funcionales: tiempos de respuesta (RNF-03) y costo de armar el estado."""

import time

import pytest

from app.dominio import sabotajes
from app.dominio.partida import Partida
from tests.conftest import RelojFalso, crear_preguntas

pytestmark = [pytest.mark.sistema, pytest.mark.no_funcional, pytest.mark.api]

LIMITE_RESPONDER_S = 0.5  # RNF-03
LIMITE_ESTADO_MEDIO_S = 0.050


def test_responder_tarda_menos_de_medio_segundo(cliente, partida_creada):
    pin, token = partida_creada["pin"], partida_creada["token_host"]
    cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Ana"})
    cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Beto"})
    cliente.post(f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": token})

    inicio = time.perf_counter()
    respuesta = cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": 0})
    duracion = time.perf_counter() - inicio

    assert respuesta.status_code == 200
    assert duracion < LIMITE_RESPONDER_S, f"POST /respuestas tardó {duracion:.3f} s (RNF-03: < 0,5 s)"


def test_estado_con_100_jugadores_es_rapido():
    partida = Partida(pin="123456", preguntas=crear_preguntas(), reloj=RelojFalso())
    partida.max_jugadores = 100
    for numero in range(100):
        partida.unirse(f"Jugador{numero:03d}")
    partida.iniciar()
    for numero in range(0, 100, 2):
        partida.responder(f"Jugador{numero:03d}", 0)
    partida.siguiente()  # RESULTADOS: el estado incluye el ranking completo

    repeticiones = 50
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        estado = partida.estado_publico()
    media = (time.perf_counter() - inicio) / repeticiones

    assert len(estado["ranking"]) == 100
    assert media < LIMITE_ESTADO_MEDIO_S, (
        f"estado_publico tardó {media * 1000:.2f} ms de media (límite 50 ms)"
    )


@pytest.mark.sabotajes
def test_mutante_respuesta_lenta_retrasa_solo_cuando_esta_activo(cliente, partida_creada, monkeypatch):
    """Comprueba la conexión del mutante con un retardo corto (0,3 s) para no alargar la suite."""
    monkeypatch.setattr(sabotajes, "RETARDO_RESPUESTA_LENTA_S", 0.3)
    pin, token = partida_creada["pin"], partida_creada["token_host"]
    for nombre in ("Ana", "Beto", "Caro"):
        cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": nombre})
    cliente.post(f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": token})
    sabotajes.desactivar_todos()

    def medir(nombre: str) -> float:
        inicio = time.perf_counter()
        cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": nombre, "opcion": 0})
        return time.perf_counter() - inicio

    assert medir("Ana") < 0.3
    sabotajes.activar("respuesta_lenta")
    assert medir("Beto") >= 0.3
