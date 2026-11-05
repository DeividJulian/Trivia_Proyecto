"""Modelos del dominio: estados, preguntas, respuestas y jugadores."""

from enum import StrEnum


class EstadoPartida(StrEnum):
    """Fases por las que pasa una partida."""

    LOBBY = "LOBBY"
    PREGUNTA = "PREGUNTA"
    RESULTADOS = "RESULTADOS"
    FINALIZADA = "FINALIZADA"
