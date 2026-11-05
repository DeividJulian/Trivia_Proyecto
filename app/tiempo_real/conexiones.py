"""Conexiones WebSocket agrupadas por PIN y difusión del estado de cada partida."""

import logging
from collections import defaultdict
from typing import Any, Protocol

logger = logging.getLogger("testquiz.tiempo_real")


class Socket(Protocol):
    """Lo mínimo que se necesita de un WebSocket (permite probar con dobles)."""

    async def send_json(self, data: Any) -> None: ...


class GestorConexiones:
    """Lleva los sockets conectados a cada partida y les envía mensajes."""

    def __init__(self) -> None:
        self._sockets: dict[str, set[Socket]] = defaultdict(set)

    def conectar(self, pin: str, socket: Socket) -> None:
        self._sockets[pin].add(socket)

    def desconectar(self, pin: str, socket: Socket) -> None:
        sockets = self._sockets.get(pin)
        if sockets is None:
            return
        sockets.discard(socket)
        if not sockets:
            del self._sockets[pin]

    def total(self, pin: str | None = None) -> int:
        """Número de conexiones abiertas (de una partida o de todas)."""
        if pin is not None:
            return len(self._sockets.get(pin, ()))
        return sum(len(sockets) for sockets in self._sockets.values())

    async def difundir(self, pin: str, mensaje: dict[str, Any]) -> int:
        """Envía el mensaje a todos los sockets de la partida y devuelve a cuántos llegó.

        Un socket cerrado o con error se elimina sin afectar el envío a los demás.
        """
        entregados = 0
        for socket in list(self._sockets.get(pin, ())):
            try:
                await socket.send_json(mensaje)
                entregados += 1
            except Exception:  # cualquier fallo de un socket solo debe sacarlo a él
                logger.info("Socket cerrado en la partida %s: se elimina de la difusión.", pin)
                self.desconectar(pin, socket)
        return entregados
