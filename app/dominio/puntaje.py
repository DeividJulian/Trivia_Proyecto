"""Reglas de puntaje del juego (v2: con bono por velocidad, SOLICITUD_CAMBIO_001)."""

from app.dominio import sabotajes

PUNTOS_BASE = 1000
BONO_VELOCIDAD_MAX = 500
BONO_POR_RACHA = 100
BONO_RACHA_MAX = 500


def es_respuesta_a_tiempo(tiempo_respuesta: float, tiempo_limite: float) -> bool:
    """Una respuesta está a tiempo si llega en el límite o antes: el límite exacto SÍ cuenta."""
    if sabotajes.esta_activo("tiempo_estricto"):
        return tiempo_respuesta < tiempo_limite  # MUTANTE: < en vez de <=
    return tiempo_respuesta <= tiempo_limite


def calcular_bono_velocidad(tiempo_respuesta: float, tiempo_limite: float) -> int:
    """Bono proporcional al tiempo que sobró: 500 al instante, 250 a mitad de tiempo, 0 al límite."""
    if tiempo_limite <= 0:
        return 0
    restante = max(0.0, tiempo_limite - max(0.0, tiempo_respuesta))
    return round(BONO_VELOCIDAD_MAX * restante / tiempo_limite)


def sumar_racha(racha: int, acerto: bool) -> int:
    """Nueva racha: suma uno si acierta y vuelve a cero si falla."""
    return racha + 1 if acerto else 0


def calcular_bono_racha(racha: int) -> int:
    """Bono por racha: desde el 2.º acierto seguido suma 100 por acierto, con tope de 500.

    `racha` es el número de aciertos seguidos contando el actual.
    """
    if racha < 2:
        return 0
    return min(BONO_POR_RACHA * (racha - 1), BONO_RACHA_MAX)


def calcular_puntos(
    opcion_correcta: bool, tiempo_respuesta: float, tiempo_limite: float, racha: int
) -> tuple[int, int]:
    """Calcula los puntos de una respuesta y la nueva racha.

    `racha` es la que traía el jugador antes de responder. Una respuesta incorrecta o fuera de
    tiempo da 0 puntos y reinicia la racha. Devuelve la tupla (puntos, nueva_racha).
    """
    acerto = opcion_correcta and es_respuesta_a_tiempo(tiempo_respuesta, tiempo_limite)
    nueva_racha = sumar_racha(racha, acerto)
    if not acerto:
        return 0, nueva_racha  # incorrecta o tarde: 0, sin bono de ningún tipo (DEF-011)
    bono_velocidad = calcular_bono_velocidad(tiempo_respuesta, tiempo_limite)
    return PUNTOS_BASE + bono_velocidad + calcular_bono_racha(nueva_racha), nueva_racha
