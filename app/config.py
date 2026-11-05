"""Configuración de la aplicación leída desde variables de entorno."""

import os
from dataclasses import dataclass

VERSION = "1.0.0"


@dataclass(frozen=True)
class Configuracion:
    """Valores de configuración del servidor."""

    admin_token: str = ""
    permitir_sabotaje: bool = True
    max_partidas: int = 500
    partida_ttl_minutos: int = 30


def cargar_configuracion() -> Configuracion:
    """Construye la configuración a partir de las variables de entorno.

    ADMIN_TOKEN es vacío por defecto: con un token vacío el panel de administrador rechaza
    todas las peticiones (queda bloqueado).
    """
    admin_token = os.environ.get("ADMIN_TOKEN", "").strip()
    return Configuracion(admin_token=admin_token)
