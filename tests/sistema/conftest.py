"""Fixtures de nivel de sistema: la aplicación completa con un gestor y un reloj controlados."""

import pytest
from fastapi.testclient import TestClient

from app.config import Configuracion
from app.dominio.gestor import GestorPartidas
from app.main import crear_app
from tests.conftest import crear_preguntas
from tests.valores_prueba import TOKEN_ADMIN_PRUEBA


@pytest.fixture
def gestor(reloj) -> GestorPartidas:
    return GestorPartidas(reloj=reloj, cargador=lambda _categoria: crear_preguntas())


@pytest.fixture
def cliente(gestor) -> TestClient:
    app = crear_app(gestor=gestor, config=Configuracion(admin_token=TOKEN_ADMIN_PRUEBA))
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def partida_creada(cliente) -> dict:
    """Crea una partida por HTTP y devuelve {"pin": ..., "token_host": ..., "estado": ...}."""
    return cliente.post("/api/partidas").json()
