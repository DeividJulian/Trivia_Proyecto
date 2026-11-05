"""Partida: máquina de estados de una trivia en vivo."""

import time
from collections.abc import Callable, Sequence

from app.dominio.errores import ErrorPartida
from app.dominio.modelos import NUMERO_OPCIONES, EstadoPartida, Jugador, Pregunta, Respuesta
from app.dominio.puntaje import calcular_puntos

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

    # --- Flujo del juego ---------------------------------------------------------------------------

    def _mostrar_pregunta(self, indice: int) -> None:
        """Pasa a la pregunta indicada y arranca su cronómetro."""
        self.indice_pregunta = indice
        self.estado = EstadoPartida.PREGUNTA
        self._inicio_pregunta = self._reloj()
        self.respuestas = {}
        self.puntos_ronda = {}

    def iniciar(self) -> None:
        """LOBBY → PREGUNTA. Exige al menos un jugador."""
        if self.estado != EstadoPartida.LOBBY:
            raise ErrorPartida("La partida ya fue iniciada.")
        if not self.jugadores:
            raise ErrorPartida("Se necesita al menos un jugador para iniciar.")
        self._mostrar_pregunta(0)
        self._tocar()

    def tiempo_transcurrido(self) -> float:
        """Segundos desde que se mostró la pregunta actual."""
        if self._inicio_pregunta is None:
            return 0.0
        return max(0.0, self._reloj() - self._inicio_pregunta)

    def tiempo_restante(self) -> float:
        """Segundos que quedan para responder (0 fuera del estado PREGUNTA)."""
        pregunta = self.pregunta_actual
        if self.estado != EstadoPartida.PREGUNTA or pregunta is None:
            return 0.0
        return max(0.0, pregunta.tiempo_limite - self.tiempo_transcurrido())

    def responder(self, nombre: str, opcion: int) -> int:
        """Registra la respuesta de un jugador y devuelve los puntos que ganó.

        Solo en PREGUNTA y una vez por jugador. Una respuesta fuera de tiempo se acepta pero vale 0
        y reinicia la racha. Si ya respondieron todos, la pregunta se cierra sola.
        """
        if self.estado != EstadoPartida.PREGUNTA:
            raise ErrorPartida("Solo se puede responder mientras hay una pregunta abierta.")
        jugador = self.buscar_jugador(nombre)
        if jugador is None:
            raise ErrorPartida(f"'{nombre}' no está en la partida.")
        if not 0 <= opcion < NUMERO_OPCIONES:
            raise ErrorPartida(f"La opción debe estar entre 0 y {NUMERO_OPCIONES - 1}.")
        if jugador.nombre in self.respuestas:
            raise ErrorPartida(f"{jugador.nombre} ya respondió esta pregunta.")

        pregunta = self.pregunta_actual
        tiempo = self.tiempo_transcurrido()
        puntos, jugador.racha = calcular_puntos(
            opcion == pregunta.correcta, tiempo, pregunta.tiempo_limite, jugador.racha
        )
        jugador.puntos += puntos
        jugador.tiempo_total += tiempo
        self.respuestas[jugador.nombre] = Respuesta(opcion=opcion, tiempo_respuesta=tiempo)
        self.puntos_ronda[jugador.nombre] = puntos
        self._tocar()

        if len(self.respuestas) == len(self.jugadores):
            self.cerrar_pregunta()
        return puntos

    def cerrar_pregunta(self) -> None:
        """PREGUNTA → RESULTADOS. Quien no respondió pierde la racha."""
        if self.estado != EstadoPartida.PREGUNTA:
            raise ErrorPartida("No hay una pregunta abierta para cerrar.")
        for jugador in self.jugadores.values():
            if jugador.nombre not in self.respuestas:
                jugador.racha = 0
        self.estado = EstadoPartida.RESULTADOS
        self._tocar()

    def siguiente(self) -> None:
        """Avanza la partida: PREGUNTA → RESULTADOS, y RESULTADOS → PREGUNTA o FINALIZADA."""
        if self.estado == EstadoPartida.PREGUNTA:
            self.cerrar_pregunta()
        elif self.estado == EstadoPartida.RESULTADOS:
            if self.indice_pregunta + 1 < len(self.preguntas):
                self._mostrar_pregunta(self.indice_pregunta + 1)
            else:
                self.estado = EstadoPartida.FINALIZADA
            self._tocar()
        else:
            raise ErrorPartida(f"No se puede avanzar desde el estado {self.estado}.")
