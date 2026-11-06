"""Prueba de carga de TestQuiz con Locust.

Simula una clase real:
  - Presentador (1 de cada ~20 usuarios): crea una partida, espera a que se unan jugadores,
    la inicia y avanza las preguntas hasta el final; luego crea otra.
  - Jugador: se une a una partida abierta, consulta el estado y responde cuando hay pregunta.

Uso (CMD, con el servidor en otra terminal):
  locust -f performance\\locustfile.py --host http://localhost:8000 --headless -u 50 -r 10 -t 2m ^
         --csv performance\\resultados\\carga_local

Los códigos 409 esperados por el juego (ya respondió, la pregunta se cerró, partida llena o
iniciada) se marcan como éxito: no son fallos del servidor sino reglas del juego.
"""

import itertools
import random
import threading
from collections import deque

import gevent
from locust import HttpUser, between, events, task

ESPERA_LOBBY_S = 5.0
MAX_ESPERAS_LOBBY = 6  # DEF-016: el presentador espera jugadores hasta 30 s antes de rendirse
SEGUNDOS_POR_PREGUNTA = 3.0

_partidas_abiertas: deque[str] = deque()
_candado = threading.Lock()
_contador_nombres = itertools.count(1)


def publicar_partida(pin: str) -> None:
    with _candado:
        _partidas_abiertas.append(pin)


def retirar_partida(pin: str) -> None:
    with _candado:
        if pin in _partidas_abiertas:
            _partidas_abiertas.remove(pin)


def partida_abierta() -> str | None:
    with _candado:
        # DEF-016: elegir al azar reparte a los jugadores entre todas las partidas abiertas
        return random.choice(_partidas_abiertas) if _partidas_abiertas else None  # noqa: S311 - simulación


@events.test_start.add_listener
def _reiniciar(**_kwargs) -> None:
    with _candado:
        _partidas_abiertas.clear()


class Presentador(HttpUser):
    """El profesor: crea partidas y las hace avanzar."""

    weight = 1
    wait_time = between(0.5, 1.0)

    @task
    def dirigir_partida(self) -> None:
        respuesta = self.client.post("/api/partidas", name="POST /api/partidas")
        if respuesta.status_code != 201:
            return
        datos = respuesta.json()
        pin, cabeceras = datos["pin"], {"X-Host-Token": datos["token_host"]}
        publicar_partida(pin)
        for _ in range(MAX_ESPERAS_LOBBY):  # DEF-016: no abandonar la partida mientras no tenga jugadores
            self.wait_seconds(ESPERA_LOBBY_S)
            lobby = self.client.get(f"/api/partidas/{pin}", name="GET /api/partidas/{pin}")
            if lobby.status_code == 200 and lobby.json()["jugadores"]:
                break
        retirar_partida(pin)

        with self.client.post(
            f"/api/partidas/{pin}/iniciar", headers=cabeceras, name="POST /iniciar", catch_response=True
        ) as iniciada:
            if iniciada.status_code == 409:  # nadie se unió
                iniciada.success()
                return
            if iniciada.status_code != 200:  # DEF-015: si no se inició, avanzar solo genera 409 falsos
                return
        estado = "PREGUNTA"
        while estado != "FINALIZADA":
            self.wait_seconds(SEGUNDOS_POR_PREGUNTA)
            avance = self.client.post(
                f"/api/partidas/{pin}/siguiente", headers=cabeceras, name="POST /siguiente"
            )
            if avance.status_code != 200:
                return
            estado = avance.json()["estado"]

    def wait_seconds(self, segundos: float) -> None:
        gevent.sleep(segundos)


class Jugador(HttpUser):
    """Un estudiante: se une, mira el estado y responde."""

    weight = 20
    wait_time = between(1, 2)

    def on_start(self) -> None:
        self.pin: str | None = None
        self.nombre = f"J{next(_contador_nombres)}"

    def _unirse(self) -> None:
        pin = partida_abierta()
        if pin is None:
            return
        with self.client.post(
            f"/api/partidas/{pin}/jugadores",
            json={"nombre": self.nombre},
            name="POST /jugadores",
            catch_response=True,
        ) as respuesta:
            if respuesta.status_code == 201:
                self.pin = pin
            elif respuesta.status_code == 409:  # partida iniciada o llena: buscará otra
                respuesta.success()

    @task
    def jugar(self) -> None:
        if self.pin is None:
            self._unirse()
            return
        with self.client.get(
            f"/api/partidas/{self.pin}", name="GET /api/partidas/{pin}", catch_response=True
        ) as r:
            if r.status_code == 404:  # la partida se limpió
                r.success()
                self.pin = None
                return
            if r.status_code != 200:
                return
            estado = r.json()
        if estado["estado"] == "FINALIZADA":
            self.pin = None
        elif estado["estado"] == "PREGUNTA" and random.random() < 0.7:  # noqa: S311 - simulación, no seguridad
            self._responder()

    def _responder(self) -> None:
        cuerpo = {"nombre": self.nombre, "opcion": random.randint(0, 3)}  # noqa: S311 - simulación
        with self.client.post(
            f"/api/partidas/{self.pin}/respuestas", json=cuerpo, name="POST /respuestas", catch_response=True
        ) as respuesta:
            if respuesta.status_code == 409:  # ya respondió o la pregunta se cerró
                respuesta.success()
