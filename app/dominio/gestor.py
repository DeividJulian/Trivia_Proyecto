"""Gestor de las partidas activas en memoria."""

import secrets
import time
from collections.abc import Callable

from app.dominio.errores import AccesoDenegado, ErrorPartida, PartidaNoEncontrada
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
        max_partidas: int = 500,
    ) -> None:
        self.max_partidas = max_partidas
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

    def obtener(self, pin: str) -> Partida:
        """Devuelve la partida del PIN o lanza PartidaNoEncontrada."""
        partida = self._partidas.get(pin)
        if partida is None:
            raise PartidaNoEncontrada(pin)
        return partida

    def validar_host(self, pin: str, token: str | None) -> Partida:
        """Comprueba el token del anfitrión en tiempo constante (compare_digest) y devuelve la partida."""
        partida = self.obtener(pin)
        esperado = self._tokens_host[pin]
        if not token or not secrets.compare_digest(token.encode(), esperado.encode()):
            raise AccesoDenegado("Token de anfitrión inválido: solo quien creó la partida puede controlarla.")
        return partida

    def crear(self, categoria: str = "pruebas") -> tuple[Partida, str]:
        """Crea una partida y devuelve la partida y el token del anfitrión.

        Lanza ErrorPartida si ya se alcanzó el máximo de partidas simultáneas.
        """
        if len(self._partidas) >= self.max_partidas:
            raise ErrorPartida(
                f"Se alcanzó el máximo de {self.max_partidas} partidas simultáneas. Intenta más tarde."
            )
        partida = Partida(pin=self._nuevo_pin(), preguntas=self._cargador(categoria), reloj=self._reloj)
        token_host = secrets.token_urlsafe(24)
        self._partidas[partida.pin] = partida
        self._tokens_host[partida.pin] = token_host
        return partida, token_host
