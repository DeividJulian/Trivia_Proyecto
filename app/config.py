"""Configuración de la aplicación leída desde variables de entorno."""

from dataclasses import dataclass

VERSION = "1.0.0"


@dataclass(frozen=True)
class Configuracion:
    """Valores de configuración del servidor."""

    admin_token: str = ""
    permitir_sabotaje: bool = True
    max_partidas: int = 500
    partida_ttl_minutos: int = 30
