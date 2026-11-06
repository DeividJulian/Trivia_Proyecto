"""Pruebas de sistema (no funcionales, de seguridad) de las cabeceras HTTP y la fábrica de la app."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.config import Configuracion
from app.main import CABECERAS_SEGURIDAD, crear_app
from tests.valores_prueba import OTRO_TOKEN_PRUEBA, TOKEN_ADMIN_PRUEBA

pytestmark = [pytest.mark.sistema, pytest.mark.seguridad, pytest.mark.api]


def test_respuestas_incluyen_cabeceras_de_seguridad():
    cliente = TestClient(crear_app(config=Configuracion(admin_token=TOKEN_ADMIN_PRUEBA)))

    respuesta = cliente.get("/salud")

    assert respuesta.headers["X-Content-Type-Options"] == "nosniff"
    assert respuesta.headers["X-Frame-Options"] == "DENY"
    assert respuesta.headers["Referrer-Policy"] == "no-referrer"


def test_cabeceras_tambien_en_rutas_inexistentes():
    cliente = TestClient(crear_app(config=Configuracion(admin_token=TOKEN_ADMIN_PRUEBA)))

    respuesta = cliente.get("/no-existe")

    assert respuesta.status_code == 404
    for nombre, valor in CABECERAS_SEGURIDAD.items():
        assert respuesta.headers[nombre] == valor


def test_avisa_en_el_log_si_no_hay_admin_token(caplog):
    with caplog.at_level(logging.WARNING, logger="testquiz"):
        crear_app(config=Configuracion(admin_token=""))

    assert "ADMIN_TOKEN no está configurado" in caplog.text


def test_admin_token_explicito_reemplaza_al_de_la_configuracion():
    app = crear_app(admin_token=OTRO_TOKEN_PRUEBA, config=Configuracion(admin_token=TOKEN_ADMIN_PRUEBA))

    assert app.state.config.admin_token == OTRO_TOKEN_PRUEBA
