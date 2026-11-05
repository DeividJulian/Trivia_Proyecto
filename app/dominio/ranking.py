"""Ordenamiento del ranking y elección del ganador."""

from collections.abc import Iterable
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


def ordenar_ranking(jugadores: Iterable[Jugador]) -> list[FilaRanking]:
    """Devuelve el ranking ordenado con las posiciones numeradas desde 1."""
    ordenados = sorted(jugadores, key=clave_orden)
    return [
        FilaRanking(
            posicion=posicion,
            nombre=jugador.nombre,
            puntos=jugador.puntos,
            tiempo_total=round(jugador.tiempo_total, 3),
        )
        for posicion, jugador in enumerate(ordenados, start=1)
    ]


def obtener_ganador(jugadores: Iterable[Jugador]) -> FilaRanking | None:
    """Primer lugar del ranking, o None si no hay jugadores."""
    ranking = ordenar_ranking(jugadores)
    return ranking[0] if ranking else None
