"""Configuración de la aplicación leída desde variables de entorno."""

import os
from dataclasses import dataclass

VERSION = "1.0.0"

VALORES_VERDADEROS = {"1", "true", "si", "sí", "yes", "on"}
VALORES_FALSOS = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Configuracion:
    """Valores de configuración del servidor."""

    admin_token: str = ""
    permitir_sabotaje: bool = True
    max_partidas: int = 500
    partida_ttl_minutos: int = 30


def _leer_booleano(nombre: str, por_defecto: bool) -> bool:
    """Lee una variable true/false; si no existe o está vacía usa el valor por defecto."""
    valor = os.environ.get(nombre, "").strip().lower()
    if not valor:
        return por_defecto
    if valor in VALORES_VERDADEROS:
        return True
    if valor in VALORES_FALSOS:
        return False
    raise ValueError(f"La variable {nombre} debe ser true o false y vale '{valor}'.")


def _leer_entero_positivo(nombre: str, por_defecto: int) -> int:
    """Lee una variable entera mayor que cero; si no existe o está vacía usa el valor por defecto."""
    valor = os.environ.get(nombre, "").strip()
    if not valor:
        return por_defecto
    try:
        numero = int(valor)
    except ValueError:
        raise ValueError(f"La variable {nombre} debe ser un número entero y vale '{valor}'.") from None
    if numero < 1:
        raise ValueError(f"La variable {nombre} debe ser mayor que cero y vale {numero}.")
    return numero


def cargar_configuracion() -> Configuracion:
    """Construye la configuración a partir de las variables de entorno.

    ADMIN_TOKEN es vacío por defecto: con un token vacío el panel de administrador rechaza
    todas las peticiones (queda bloqueado).
    """
    return Configuracion(
        admin_token=os.environ.get("ADMIN_TOKEN", "").strip(),
        permitir_sabotaje=_leer_booleano("PERMITIR_SABOTAJE", True),
        max_partidas=_leer_entero_positivo("MAX_PARTIDAS", 500),
        partida_ttl_minutos=_leer_entero_positivo("PARTIDA_TTL_MINUTOS", 30),
    )
