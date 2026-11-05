"""Gestor de las partidas activas en memoria."""

import secrets
import time
from collections.abc import Callable

from app.dominio.modelos import Pregunta
from app.dominio.partida import Partida, Reloj
from app.dominio.preguntas import cargar_preguntas

DIGITOS_PIN = 6


class GestorPartidas:
    """Crea partidas con un PIN único de 6 dígitos y un token secreto para el anfitrión."""

    def __init__(
        self,
        reloj: Reloj = time.monotonic,
        cargador: Callable[[str], list[Pregunta]] = cargar_preguntas,
    ) -> None:
        self._reloj = reloj
        self._cargador = cargador
        self._partidas: dict[str, Partida] = {}
        self._tokens_host: dict[str, str] = {}

    def __len__(self) -> int:
        return len(self._partidas)

    def _nuevo_pin(self) -> str:
        """PIN aleatorio de 6 dígitos (secrets, no random) que no esté en uso."""
        while True:
            pin = f"{secrets.randbelow(10**DIGITOS_PIN):0{DIGITOS_PIN}d}"
            if pin not in self._partidas:
                return pin

    def crear(self, categoria: str = "pruebas") -> tuple[Partida, str]:
        """Crea una partida y devuelve la partida y el token del anfitrión."""
        partida = Partida(pin=self._nuevo_pin(), preguntas=self._cargador(categoria), reloj=self._reloj)
        token_host = secrets.token_urlsafe(24)
        self._partidas[partida.pin] = partida
        self._tokens_host[partida.pin] = token_host
        return partida, token_host
