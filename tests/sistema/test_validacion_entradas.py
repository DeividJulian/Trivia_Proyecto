"""Pruebas de sistema de validación de entradas, nacidas de las sesiones exploratorias."""

import pytest

pytestmark = [pytest.mark.sistema, pytest.mark.api]


@pytest.mark.parametrize("nombre", ["   ", "\t"])
def test_nombre_solo_con_espacios_responde_422(cliente, partida_creada, nombre):
    """DEF-008: un nombre vacío tras quitar espacios es una entrada inválida (422), no un conflicto (409)."""
    respuesta = cliente.post(f"/api/partidas/{partida_creada['pin']}/jugadores", json={"nombre": nombre})

    assert respuesta.status_code == 422


def test_nombre_con_espacios_alrededor_se_recorta(cliente, partida_creada):
    respuesta = cliente.post(f"/api/partidas/{partida_creada['pin']}/jugadores", json={"nombre": "  Ana  "})

    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == "Ana"


@pytest.mark.parametrize("opcion", [True, False, "2", 1.0])
def test_opcion_debe_ser_un_entero_estricto(cliente, partida_creada, opcion):
    """DEF-009: true, "2" o 1.0 no son opciones válidas; antes true contaba como la opción 1."""
    pin = partida_creada["pin"]
    cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Ana"})
    cliente.post(f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": partida_creada["token_host"]})

    respuesta = cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": opcion})

    assert respuesta.status_code == 422
    assert cliente.get(f"/api/partidas/{pin}/jugadores/Ana").json()["puntos"] == 0


@pytest.mark.parametrize("pin", ["abc", "12345", "1234567", "9" * 300])
def test_pin_con_formato_invalido_responde_422_sin_repetir_la_entrada(cliente, pin):
    """DEF-010: el PIN debe tener 6 dígitos; la respuesta no debe devolver textos arbitrarios largos."""
    respuesta = cliente.get(f"/api/partidas/{pin}")

    assert respuesta.status_code == 422
    assert len(respuesta.text) < 400


def test_websocket_con_pin_largo_se_cierra_con_4404(cliente):
    from starlette.websockets import WebSocketDisconnect

    with (
        cliente.websocket_connect("/ws/" + "9" * 300) as socket,
        pytest.raises(WebSocketDisconnect) as cierre,
    ):
        socket.receive_json()

    assert cierre.value.code == 4404
