"""Prueba de sistema del endpoint de salud."""

import pytest
from fastapi.testclient import TestClient

from app.main import VERSION, app

pytestmark = [pytest.mark.sistema, pytest.mark.api]


def test_salud_responde_ok_con_la_version():
    cliente = TestClient(app)

    respuesta = cliente.get("/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "version": VERSION}
