"""Fixtures compartidas por todas las pruebas."""

import pytest

from app.dominio.modelos import Pregunta
from app.dominio.partida import Partida

LIMITE = 20.0


class RelojFalso:
    """Reloj controlable: reemplaza a time.monotonic para avanzar el tiempo sin esperar."""

    def __init__(self, inicio: float = 1000.0) -> None:
        self.ahora = inicio

    def __call__(self) -> float:
        return self.ahora

    def avanzar(self, segundos: float) -> None:
        self.ahora += segundos


def crear_preguntas(cantidad: int = 3, limite: float = LIMITE) -> list[Pregunta]:
    """Preguntas de prueba: la respuesta correcta de la pregunta i es la opción i % 4."""
    return [
        Pregunta(
            texto=f"Pregunta {i + 1}",
            opciones=("A", "B", "C", "D"),
            correcta=i % 4,
            tiempo_limite=limite,
        )
        for i in range(cantidad)
    ]


@pytest.fixture
def reloj() -> RelojFalso:
    return RelojFalso()


@pytest.fixture
def preguntas() -> list[Pregunta]:
    return crear_preguntas()


@pytest.fixture
def partida(reloj, preguntas) -> Partida:
    return Partida(pin="123456", preguntas=preguntas, reloj=reloj)


@pytest.fixture
def partida_con_jugadores(partida) -> Partida:
    for nombre in ("Ana", "Beto", "Caro"):
        partida.unirse(nombre)
    return partida
