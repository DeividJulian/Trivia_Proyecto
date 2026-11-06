"""Prueba de sistema del endpoint de salud."""

import pytest
from fastapi.testclient import TestClient

from app.config import Configuracion
from app.main import VERSION, app, crear_app

pytestmark = [pytest.mark.sistema, pytest.mark.api]


def test_salud_responde_ok_con_la_version():
    cliente = TestClient(app)

    respuesta = cliente.get("/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "version": VERSION, "commit": app.state.config.commit}


def test_salud_informa_el_commit_del_despliegue():
    cliente = TestClient(crear_app(config=Configuracion(commit="abc123")))

    respuesta = cliente.get("/salud")

    assert respuesta.json()["commit"] == "abc123"
