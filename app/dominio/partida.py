"""Partida: máquina de estados de una trivia en vivo."""

import time
from collections.abc import Callable, Sequence

from app.dominio.errores import ErrorPartida
from app.dominio.modelos import EstadoPartida, Jugador, Pregunta, Respuesta

Reloj = Callable[[], float]

LONGITUD_MAX_NOMBRE = 20
MAX_JUGADORES_POR_DEFECTO = 50


class Partida:
    """Una partida identificada por su PIN.

    El reloj se inyecta (por defecto time.monotonic) para que las pruebas controlen el tiempo
    sin esperar de verdad.
    """

    def __init__(
        self,
        pin: str,
        preguntas: Sequence[Pregunta],
        reloj: Reloj = time.monotonic,
        max_jugadores: int = MAX_JUGADORES_POR_DEFECTO,
    ) -> None:
        if not preguntas:
            raise ValueError("Una partida necesita al menos una pregunta.")
        self.pin = pin
        self.preguntas = list(preguntas)
        self.max_jugadores = max_jugadores
        self._reloj = reloj
        self.estado = EstadoPartida.LOBBY
        self.jugadores: dict[str, Jugador] = {}
        self.indice_pregunta = -1
        self.respuestas: dict[str, Respuesta] = {}
        self.puntos_ronda: dict[str, int] = {}
        self._inicio_pregunta: float | None = None
        self.ultima_actividad = reloj()

    def _tocar(self) -> None:
        """Registra actividad (la usa el gestor para limpiar partidas inactivas)."""
        self.ultima_actividad = self._reloj()

    @property
    def pregunta_actual(self) -> Pregunta | None:
        """Pregunta en curso, o None si la partida no ha empezado."""
        if 0 <= self.indice_pregunta < len(self.preguntas):
            return self.preguntas[self.indice_pregunta]
        return None

    def buscar_jugador(self, nombre: str) -> Jugador | None:
        """Busca un jugador sin distinguir mayúsculas de minúsculas ni espacios en los extremos."""
        clave = (nombre or "").strip().casefold()
        for jugador in self.jugadores.values():
            if jugador.nombre.casefold() == clave:
                return jugador
        return None

    def unirse(self, nombre: str) -> Jugador:
        """Agrega un jugador: solo en LOBBY, nombre de 1 a 20 caracteres, sin repetir y con cupo."""
        if self.estado != EstadoPartida.LOBBY:
            raise ErrorPartida("La partida ya comenzó: no se admiten más jugadores.")
        nombre = (nombre or "").strip()
        if not 1 <= len(nombre) <= LONGITUD_MAX_NOMBRE:
            raise ErrorPartida(f"El nombre debe tener entre 1 y {LONGITUD_MAX_NOMBRE} caracteres.")
        if self.buscar_jugador(nombre) is not None:
            raise ErrorPartida(f"Ya hay un jugador llamado '{nombre}' en la partida.")
        if len(self.jugadores) >= self.max_jugadores:
            raise ErrorPartida(f"La partida está llena: máximo {self.max_jugadores} jugadores.")
        jugador = Jugador(nombre=nombre)
        self.jugadores[nombre] = jugador
        self._tocar()
        return jugador
