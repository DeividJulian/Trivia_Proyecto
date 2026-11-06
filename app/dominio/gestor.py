"""Gestor de las partidas activas en memoria."""

import secrets
import time
from collections.abc import Callable

from app.dominio.errores import AccesoDenegado, ErrorPartida, PartidaNoEncontrada
from app.dominio.modelos import EstadoPartida, Pregunta
from app.dominio.partida import Partida, Reloj
from app.dominio.preguntas import cargar_preguntas

DIGITOS_PIN = 6
MINUTOS_GRACIA_FINALIZADA = 5


class GestorPartidas:
    """Crea partidas con un PIN único de 6 dígitos y un token secreto para el anfitrión."""

    def __init__(
        self,
        reloj: Reloj = time.monotonic,
        cargador: Callable[[str], list[Pregunta]] = cargar_preguntas,
        max_partidas: int = 500,
        ttl_minutos: int = 30,
    ) -> None:
        self.max_partidas = max_partidas
        self.ttl_minutos = ttl_minutos
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

    def limpiar(self) -> int:
        """Elimina las partidas inactivas y devuelve cuántas se eliminaron.

        Una partida en curso se elimina tras PARTIDA_TTL_MINUTOS sin actividad; una FINALIZADA,
        antes (a los 5 minutos, o al TTL si es menor), para liberar memoria sin cortar el podio.
        """
        ahora = self._reloj()
        ttl = self.ttl_minutos * 60
        ttl_finalizada = min(ttl, MINUTOS_GRACIA_FINALIZADA * 60)
        vencidas = [
            pin
            for pin, partida in self._partidas.items()
            if ahora - partida.ultima_actividad
            > (ttl_finalizada if partida.estado == EstadoPartida.FINALIZADA else ttl)
        ]
        for pin in vencidas:
            del self._partidas[pin]
            del self._tokens_host[pin]
        return len(vencidas)

    def listar(self) -> list[Partida]:
        """Devuelve la lista de partidas activas (tras limpiar las inactivas)."""
        self.limpiar()
        return list(self._partidas.values())

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
        self.limpiar()
        if len(self._partidas) >= self.max_partidas:
            raise ErrorPartida(
                f"Se alcanzó el máximo de {self.max_partidas} partidas simultáneas. Intenta más tarde."
            )
        partida = Partida(pin=self._nuevo_pin(), preguntas=self._cargador(categoria), reloj=self._reloj)
        token_host = secrets.token_urlsafe(24)
        self._partidas[partida.pin] = partida
        self._tokens_host[partida.pin] = token_host
        return partida, token_host
