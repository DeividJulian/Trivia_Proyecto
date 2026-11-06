"""Prueba de carga REST + WebSocket.

Mismo escenario que locustfile.py (presentadores y jugadores, que NO se modifica), pero cada jugador
además mantiene abierta la conexión /ws/{pin}, como el front real. Así se mide el costo de difundir
cada respuesta a todos los jugadores de la partida.

Métricas de WebSocket (registro propio, no se mezclan con el p95 de REST de Locust):
  - conexiones abiertas y fallidas, cierres inesperados;
  - mensajes de estado recibidos (y por segundo);
  - latencia de difusión: desde que el jugador envía POST /respuestas hasta el primer mensaje
    de estado que le llega por WebSocket después.
Al terminar se escriben en <prefijo>_ws_eventos.csv (con --csv <prefijo>).

Uso (CMD, con el servidor en otra terminal):
  locust -f performance\\locustfile_ws.py --host http://127.0.0.1:8000 --headless -u 50 -r 10 -t 2m ^
         --csv performance\\resultados\\carga_ws_local
"""

import logging
import random
import sys
import time
from pathlib import Path

import gevent
import websocket
from locust import events

sys.path.insert(0, str(Path(__file__).resolve().parent))

import locustfile as base  # noqa: E402 - mismo directorio, agregado arriba a sys.path
from medidor_ws import (  # noqa: E402
    CIERRE_INESPERADO,
    CONEXION_FALLIDA,
    CONEXION_OK,
    LATENCIA,
    MENSAJE,
    MedidorDifusion,
    RegistroWS,
    parsear_mensaje,
    resumir,
    url_websocket,
)

logger = logging.getLogger("locustfile_ws")

Presentador = base.Presentador  # Locust toma los usuarios que están en este módulo

REGISTRO = RegistroWS()
_inicio = {"t": time.monotonic()}


@events.test_start.add_listener
def _al_empezar(**_kwargs) -> None:
    REGISTRO.eventos.clear()
    _inicio["t"] = time.monotonic()


@events.test_stop.add_listener
def _al_terminar(environment, **_kwargs) -> None:
    resumen = resumir(REGISTRO.eventos, time.monotonic() - _inicio["t"])
    logger.warning("WebSocket: %s", resumen)
    prefijo = getattr(environment.parsed_options, "csv_prefix", None) if environment.parsed_options else None
    if prefijo:
        REGISTRO.escribir(Path(f"{prefijo}_ws_eventos.csv"))


class JugadorWebSocket(base.Jugador):
    """Jugador que, además de usar la API REST, escucha la partida por WebSocket."""

    weight = 20

    def on_start(self) -> None:
        super().on_start()
        self.ws: websocket.WebSocket | None = None
        self.receptor: gevent.Greenlet | None = None
        self.cerrando = False
        self.medidor = MedidorDifusion()

    def on_stop(self) -> None:
        self._cerrar_ws()

    def _registrar(self, tipo: str, valor_ms: float = 0.0) -> None:
        REGISTRO.agregar(time.monotonic() - _inicio["t"], self.environment.runner.user_count, tipo, valor_ms)

    def _unirse(self) -> None:
        super()._unirse()
        if self.pin is not None and self.ws is None:
            self._conectar(self.pin)

    def jugar(self) -> None:
        super().jugar()
        if self.pin is None and self.ws is not None:  # la partida terminó o se limpió: cierre esperado
            self._cerrar_ws()

    def _responder(self) -> None:
        # Igual que Jugador._responder, pero sabiendo si el POST fue 200 (solo entonces hay difusión).
        cuerpo = {"nombre": self.nombre, "opcion": random.randint(0, 3)}  # noqa: S311 - simulación
        self.medidor.marcar_envio(time.perf_counter())
        with self.client.post(
            f"/api/partidas/{self.pin}/respuestas", json=cuerpo, name="POST /respuestas", catch_response=True
        ) as respuesta:
            exito = respuesta.status_code == 200
            if respuesta.status_code == 409:  # ya respondió o la pregunta se cerró
                respuesta.success()
        latencia = self.medidor.confirmar(exito)
        if latencia is not None:
            self._registrar(LATENCIA, latencia)

    def _conectar(self, pin: str) -> None:
        inicio = time.perf_counter()
        try:
            ws = websocket.create_connection(url_websocket(self.host, pin), timeout=10)
        except Exception:  # cualquier fallo al conectar cuenta como conexión fallida
            self._registrar(CONEXION_FALLIDA, (time.perf_counter() - inicio) * 1000)
            return
        ws.settimeout(None)  # en el lobby pueden pasar 30 s sin mensajes: no es un error
        self._registrar(CONEXION_OK, (time.perf_counter() - inicio) * 1000)
        self.ws, self.cerrando = ws, False
        self.receptor = gevent.spawn(self._recibir, ws)

    def _recibir(self, ws: websocket.WebSocket) -> None:
        while True:
            try:
                texto = ws.recv()
            except Exception:  # cierre del socket (esperado o no)
                texto = None
            if not texto:
                if not self.cerrando:
                    self._registrar(CIERRE_INESPERADO)
                return
            if parsear_mensaje(texto) is None:
                continue
            self._registrar(MENSAJE)
            latencia = self.medidor.mensaje_recibido(time.perf_counter())
            if latencia is not None:
                self._registrar(LATENCIA, latencia)

    def _cerrar_ws(self) -> None:
        ws, self.ws = self.ws, None
        if ws is None:
            return
        self.cerrando = True
        try:
            ws.close()
        except Exception:  # ya estaba cerrado
            logger.debug("El socket ya estaba cerrado.")
        if self.receptor is not None:
            self.receptor.kill(block=False)
            self.receptor = None
