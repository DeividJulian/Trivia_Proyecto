"""Pruebas de sistema (funcionales) de la API REST."""

import pytest

from app.main import crear_app

pytestmark = [pytest.mark.sistema, pytest.mark.api]


def test_crear_partida_devuelve_pin_y_token(cliente):
    respuesta = cliente.post("/api/partidas")

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert len(datos["pin"]) == 6
    assert datos["token_host"]
    assert datos["estado"] == "LOBBY"


def test_crear_partida_con_categoria(cliente, gestor):
    respuesta = cliente.post("/api/partidas", json={"categoria": "cultura"})

    assert respuesta.status_code == 201


def test_ver_partida_no_expone_el_token(cliente, partida_creada):
    respuesta = cliente.get(f"/api/partidas/{partida_creada['pin']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "LOBBY"
    assert partida_creada["token_host"] not in respuesta.text


def test_gestor_inyectado_vacio_se_respeta(gestor):
    """Regresión del "gestor or ...": un gestor vacío es falso pero debe usarse igual."""
    assert len(gestor) == 0

    app = crear_app(gestor=gestor)

    assert app.state.gestor is gestor
