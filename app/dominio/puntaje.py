"""Reglas de puntaje del juego (v1: sin bono por velocidad)."""

PUNTOS_BASE = 1000
BONO_POR_RACHA = 100
BONO_RACHA_MAX = 500


def es_respuesta_a_tiempo(tiempo_respuesta: float, tiempo_limite: float) -> bool:
    """Una respuesta está a tiempo si llega en el límite o antes: el límite exacto SÍ cuenta."""
    return tiempo_respuesta <= tiempo_limite
