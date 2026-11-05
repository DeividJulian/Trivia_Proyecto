"""Modo Saboteador: mutantes controlados.

Cada sabotaje es un "mutante": una rama alternativa del código que solo se ejecuta si
esta_activo("clave") es verdadero. El código nunca se modifica en caliente.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Sabotaje:
    """Descripción de un mutante y del nivel de prueba que debería detectarlo."""

    clave: str
    nombre: str
    modulo: str
    descripcion: str
    nivel_que_lo_detecta: str
