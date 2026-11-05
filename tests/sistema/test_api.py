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


def test_unirse_a_una_partida(cliente, partida_creada):
    pin = partida_creada["pin"]

    respuesta = cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "  Ana "})

    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == "Ana"
    assert cliente.get(f"/api/partidas/{pin}").json()["jugadores"] == ["Ana"]


def test_unirse_con_nombre_repetido_responde_409(cliente, partida_creada):
    url = f"/api/partidas/{partida_creada['pin']}/jugadores"
    cliente.post(url, json={"nombre": "Ana"})

    respuesta = cliente.post(url, json={"nombre": "ana"})

    assert respuesta.status_code == 409
    assert "Ya hay un jugador" in respuesta.json()["detail"]
