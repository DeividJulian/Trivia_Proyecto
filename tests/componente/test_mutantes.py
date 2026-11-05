"""Cada mutante cambia el comportamiento SOLO cuando está activo.

Estas pruebas comprueban que el mutante está bien conectado. Que las demás pruebas lo detecten
(lo "maten") lo verifica scripts/verificar_mutantes.py.
"""

import pytest

from app.dominio import sabotajes
from app.dominio.puntaje import es_respuesta_a_tiempo

pytestmark = [pytest.mark.componente, pytest.mark.sabotajes]


@pytest.fixture
def sin_sabotajes():
    sabotajes.desactivar_todos()


def test_tiempo_estricto(sin_sabotajes):
    assert es_respuesta_a_tiempo(20.0, 20.0) is True

    sabotajes.activar("tiempo_estricto")

    assert es_respuesta_a_tiempo(20.0, 20.0) is False
