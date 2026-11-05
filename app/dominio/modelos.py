"""Modelos del dominio: estados, preguntas, respuestas y jugadores."""

from dataclasses import dataclass
from enum import StrEnum

NUMERO_OPCIONES = 4


class EstadoPartida(StrEnum):
    """Fases por las que pasa una partida."""

    LOBBY = "LOBBY"
    PREGUNTA = "PREGUNTA"
    RESULTADOS = "RESULTADOS"
    FINALIZADA = "FINALIZADA"


@dataclass(frozen=True)
class Pregunta:
    """Pregunta de opción múltiple con exactamente cuatro opciones."""

    texto: str
    opciones: tuple[str, ...]
    correcta: int
    tiempo_limite: float = 20.0

    def __post_init__(self) -> None:
        if not self.texto or not self.texto.strip():
            raise ValueError("La pregunta debe tener texto.")
        object.__setattr__(self, "opciones", tuple(self.opciones))
        if len(self.opciones) != NUMERO_OPCIONES:
            raise ValueError(f"La pregunta debe tener exactamente {NUMERO_OPCIONES} opciones.")
        if any(not str(opcion).strip() for opcion in self.opciones):
            raise ValueError("Ninguna opción puede estar vacía.")
        if not 0 <= self.correcta < NUMERO_OPCIONES:
            raise ValueError(f"El índice correcto debe estar entre 0 y {NUMERO_OPCIONES - 1}.")
        if self.tiempo_limite <= 0:
            raise ValueError("El tiempo límite debe ser mayor que cero.")


@dataclass(frozen=True)
class Respuesta:
    """Respuesta de un jugador: opción elegida y segundos que tardó en responder."""

    opcion: int
    tiempo_respuesta: float


@dataclass
class Jugador:
    """Participante de una partida y su marcador acumulado."""

    nombre: str
    puntos: int = 0
    racha: int = 0
    tiempo_total: float = 0.0
