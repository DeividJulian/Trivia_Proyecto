"""Medición de WebSocket en las pruebas de carga (lógica pura, sin red, para poder probarla).

Las métricas de WebSocket NO se registran como peticiones de Locust: si se mezclaran con la fila
"Aggregated", el p95 de REST (RNF-01) dejaría de ser comparable entre escenarios. Se guardan en un
registro propio y se escriben en <prefijo>_ws_eventos.csv al terminar la prueba.
"""

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONEXION_OK = "conexion_ok"
CONEXION_FALLIDA = "conexion_fallida"
MENSAJE = "mensaje"
LATENCIA = "latencia_difusion"
CIERRE_INESPERADO = "cierre_inesperado"
TIPOS = (CONEXION_OK, CONEXION_FALLIDA, MENSAJE, LATENCIA, CIERRE_INESPERADO)


def url_websocket(host: str, pin: str) -> str:
    """http://127.0.0.1:8000 -> ws://127.0.0.1:8000/ws/<pin> (https -> wss)."""
    base = host.rstrip("/")
    if base.startswith("https://"):
        base = "wss://" + base.removeprefix("https://")
    elif base.startswith("http://"):
        base = "ws://" + base.removeprefix("http://")
    else:
        raise ValueError(f"El host debe empezar por http:// o https:// y es '{host}'.")
    return f"{base}/ws/{pin}"


def parsear_mensaje(texto: str | bytes) -> dict[str, Any] | None:
    """Mensaje {"tipo": ..., "datos": ...} del servidor, o None si no es JSON con esa forma."""
    try:
        mensaje = json.loads(texto)
    except (TypeError, ValueError):
        return None
    if not isinstance(mensaje, dict) or "tipo" not in mensaje:
        return None
    return mensaje


def percentil(valores: list[float], p: float) -> float | None:
    """Percentil por rango más cercano (el que usa Locust): p entre 0 y 100."""
    if not valores:
        return None
    ordenados = sorted(valores)
    indice = max(math.ceil(p / 100 * len(ordenados)) - 1, 0)
    return ordenados[indice]


class MedidorDifusion:
    """Latencia de difusión: desde que el jugador envía POST /respuestas hasta el primer mensaje
    de estado que recibe por WebSocket después de enviarlo.

    Solo cuenta si el POST respondió 200: con 409 (pregunta cerrada o respuesta repetida) el servidor
    no difunde nada y el "siguiente mensaje" sería otro evento, segundos después. El mensaje puede
    llegar antes o después de la respuesta HTTP (son conexiones distintas), por eso se espera a ambos.
    """

    def __init__(self) -> None:
        self._reiniciar()

    def _reiniciar(self) -> None:
        self._envio: float | None = None
        self._latencia: float | None = None
        self._confirmado = False

    def marcar_envio(self, instante: float) -> None:
        self._reiniciar()
        self._envio = instante

    def mensaje_recibido(self, instante: float) -> float | None:
        """Devuelve la latencia en ms si el POST ya se confirmó; si no, la guarda y devuelve None."""
        if self._envio is None or self._latencia is not None:
            return None
        self._latencia = (instante - self._envio) * 1000
        return self._emitir() if self._confirmado else None

    def confirmar(self, exito: bool) -> float | None:
        """Resultado del POST. Devuelve la latencia en ms si el mensaje ya había llegado."""
        if self._envio is None:
            return None
        if not exito:
            self._reiniciar()
            return None
        self._confirmado = True
        return self._emitir() if self._latencia is not None else None

    def _emitir(self) -> float | None:
        latencia = self._latencia
        self._reiniciar()
        return latencia


@dataclass
class Evento:
    momento: float  # segundos desde el inicio de la prueba
    usuarios: int
    tipo: str
    valor_ms: float = 0.0


@dataclass
class RegistroWS:
    eventos: list[Evento] = field(default_factory=list)

    def agregar(self, momento: float, usuarios: int, tipo: str, valor_ms: float = 0.0) -> None:
        if tipo not in TIPOS:
            raise ValueError(f"Tipo de evento desconocido: {tipo}")
        self.eventos.append(Evento(momento, usuarios, tipo, valor_ms))

    def escribir(self, ruta: Path) -> None:
        with ruta.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["momento_s", "usuarios", "tipo", "valor_ms"])
            for e in self.eventos:
                escritor.writerow([f"{e.momento:.3f}", e.usuarios, e.tipo, f"{e.valor_ms:.3f}"])


def leer_eventos(ruta: Path) -> list[Evento]:
    with ruta.open(encoding="utf-8") as archivo:
        return [
            Evento(float(f["momento_s"]), int(f["usuarios"]), f["tipo"], float(f["valor_ms"]))
            for f in csv.DictReader(archivo)
        ]


def resumir(eventos: list[Evento], duracion_s: float | None = None) -> dict[str, Any]:
    """Totales de una prueba: conexiones, mensajes (y por segundo) y latencia de difusión."""
    latencias = [e.valor_ms for e in eventos if e.tipo == LATENCIA]
    mensajes = sum(1 for e in eventos if e.tipo == MENSAJE)
    if duracion_s is None:
        duracion_s = max((e.momento for e in eventos), default=0.0)
    return {
        "conexiones_ok": sum(1 for e in eventos if e.tipo == CONEXION_OK),
        "conexiones_fallidas": sum(1 for e in eventos if e.tipo == CONEXION_FALLIDA),
        "cierres_inesperados": sum(1 for e in eventos if e.tipo == CIERRE_INESPERADO),
        "mensajes": mensajes,
        "mensajes_por_s": round(mensajes / duracion_s, 1) if duracion_s else 0.0,
        "latencias": len(latencias),
        "latencia_p50_ms": percentil(latencias, 50),
        "latencia_p95_ms": percentil(latencias, 95),
        "latencia_max_ms": max(latencias, default=None),
    }


def por_escalon(eventos: list[Evento]) -> list[dict[str, Any]]:
    """Agrupa los eventos por número de usuarios (escalones de la prueba de estrés)."""
    grupos: dict[int, list[Evento]] = {}
    for e in eventos:
        if e.usuarios > 0:
            grupos.setdefault(e.usuarios, []).append(e)
    filas = []
    for usuarios in sorted(grupos):
        grupo = grupos[usuarios]
        duracion = max(e.momento for e in grupo) - min(e.momento for e in grupo)
        fila = resumir(grupo, duracion)
        fila["usuarios"] = usuarios
        filas.append(fila)
    return filas
