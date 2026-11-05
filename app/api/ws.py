"""WebSocket /ws/{pin}: envía el estado de la partida en tiempo real."""

import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.dominio.errores import PartidaNoEncontrada

router = APIRouter()

CODIGO_PIN_INEXISTENTE = 4404
PATRON_PIN = re.compile(r"\d{6}")


@router.websocket("/ws/{pin}")
async def ws_partida(websocket: WebSocket, pin: str) -> None:
    """Al conectarse recibe el estado actual; luego, un mensaje {"tipo": "estado"} en cada acción.

    Si el PIN no existe, el socket se cierra con el código 4404.
    """
    gestor = websocket.app.state.gestor
    conexiones = websocket.app.state.conexiones
    await websocket.accept()
    if not PATRON_PIN.fullmatch(pin):
        await websocket.close(code=CODIGO_PIN_INEXISTENTE, reason="El PIN debe tener 6 dígitos.")
        return
    try:
        partida = gestor.obtener(pin)
    except PartidaNoEncontrada as error:
        await websocket.close(code=CODIGO_PIN_INEXISTENTE, reason=str(error))
        return

    conexiones.conectar(pin, websocket)
    try:
        await websocket.send_json({"tipo": "estado", "datos": partida.estado_publico()})
        while True:
            await websocket.receive_text()  # los clientes no envían órdenes: solo mantiene viva la conexión
    except WebSocketDisconnect:
        pass
    finally:
        conexiones.desconectar(pin, websocket)
