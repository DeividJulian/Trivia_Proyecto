"""Pruebas de sistema (funcionales) del WebSocket /ws/{pin}."""

import pytest
from starlette.websockets import WebSocketDisconnect

pytestmark = [pytest.mark.sistema, pytest.mark.api]


def test_websocket_recibe_el_estado_al_conectarse_al_unirse_y_al_iniciar(cliente, partida_creada):
    pin, token = partida_creada["pin"], partida_creada["token_host"]

    with cliente.websocket_connect(f"/ws/{pin}") as socket:
        inicial = socket.receive_json()
        assert inicial["tipo"] == "estado"
        assert inicial["datos"]["estado"] == "LOBBY"

        cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Ana"})
        al_unirse = socket.receive_json()
        assert al_unirse["datos"]["jugadores"] == ["Ana"]

        cliente.post(f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": token})
        al_iniciar = socket.receive_json()
        assert al_iniciar["datos"]["estado"] == "PREGUNTA"
        assert "correcta" not in al_iniciar["datos"]


def test_varios_sockets_reciben_la_misma_difusion(cliente, partida_creada):
    pin = partida_creada["pin"]

    with cliente.websocket_connect(f"/ws/{pin}") as uno, cliente.websocket_connect(f"/ws/{pin}") as dos:
        uno.receive_json()
        dos.receive_json()
        cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Beto"})

        assert uno.receive_json() == dos.receive_json()


def test_websocket_con_pin_inexistente_se_cierra_con_4404(cliente):
    with cliente.websocket_connect("/ws/000000") as socket, pytest.raises(WebSocketDisconnect) as cierre:
        socket.receive_json()

    assert cierre.value.code == 4404


def test_al_desconectarse_deja_de_contar(cliente, partida_creada):
    pin = partida_creada["pin"]
    conexiones = cliente.app.state.conexiones

    with cliente.websocket_connect(f"/ws/{pin}") as socket:
        socket.receive_json()
        assert conexiones.total(pin) == 1

    cliente.get("/salud")  # da tiempo al servidor a procesar el cierre
    assert conexiones.total(pin) == 0
