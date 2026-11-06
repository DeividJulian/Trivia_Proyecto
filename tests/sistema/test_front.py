"""Pruebas de sistema del front de demostración servido por FastAPI."""

import pytest

pytestmark = [pytest.mark.sistema, pytest.mark.api]


def test_la_raiz_sirve_el_front(cliente):
    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    assert "text/html" in respuesta.headers["content-type"]
    assert "TestQuiz" in respuesta.text
    assert respuesta.headers["X-Frame-Options"] == "DENY"


@pytest.mark.parametrize(("ruta", "tipo"), [("/app.js", "javascript"), ("/estilos.css", "text/css")])
def test_sirve_los_recursos_estaticos(cliente, ruta, tipo):
    respuesta = cliente.get(ruta)

    assert respuesta.status_code == 200
    assert tipo in respuesta.headers["content-type"]


def test_la_api_y_la_documentacion_siguen_teniendo_prioridad(cliente):
    assert cliente.get("/salud").json()["estado"] == "ok"
    assert cliente.get("/docs").status_code == 200
    assert cliente.get("/api/partidas/000000").status_code == 404
