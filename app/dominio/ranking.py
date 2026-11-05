"""Ordenamiento del ranking y elección del ganador."""

from dataclasses import dataclass

from app.dominio.modelos import Jugador


@dataclass(frozen=True)
class FilaRanking:
    """Una fila del ranking: posición, nombre, puntos y tiempo total de respuesta."""

    posicion: int
    nombre: str
    puntos: int
    tiempo_total: float


def clave_orden(jugador: Jugador) -> tuple[int, float, str]:
    """Clave de orden: más puntos primero, luego menor tiempo total y luego nombre alfabético."""
    return (-jugador.puntos, jugador.tiempo_total, jugador.nombre.casefold())
