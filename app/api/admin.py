"""Panel de administrador del modo Saboteador."""

import asyncio
import logging
import secrets
from dataclasses import asdict
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.calidad import ejecutor
from app.dominio import sabotajes
from app.dominio.sabotajes import Sabotaje

logger = logging.getLogger("testquiz.admin")


def verificar_admin(
    request: Request,
    x_admin_token: Annotated[str | None, Header(description="Token del panel (ADMIN_TOKEN).")] = None,
) -> None:
    """Protege todo el panel.

    404 si PERMITIR_SABOTAJE=false (el panel "no existe"); 403 si falta el token, si no coincide
    o si ADMIN_TOKEN está vacío en el servidor. La comparación es en tiempo constante.
    """
    config = request.app.state.config
    if not config.permitir_sabotaje:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El modo Saboteador está deshabilitado.")
    esperado = config.admin_token
    if (
        not esperado
        or not x_admin_token
        or not secrets.compare_digest(x_admin_token.encode(), esperado.encode())
    ):
        logger.warning(
            "Acceso denegado al panel de administrador desde %s.",
            request.client.host if request.client else "?",
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token de administrador inválido.")


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(verificar_admin)])


def _sabotaje_a_dict(sabotaje: Sabotaje) -> dict[str, Any]:
    return {**asdict(sabotaje), "activo": sabotajes.esta_activo(sabotaje.clave)}


def _estado() -> dict[str, Any]:
    return {
        "catalogo": [_sabotaje_a_dict(s) for s in sabotajes.CATALOGO.values()],
        "activos": sabotajes.activos(),
    }


def _validar_clave(clave: str) -> str:
    if clave not in sabotajes.CATALOGO:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe el sabotaje '{clave[:40]}'.")
    return clave


@router.get("/sabotajes")
async def ver_sabotajes() -> dict[str, Any]:
    """Catálogo de mutantes y cuáles están activos."""
    return _estado()


@router.post("/sabotajes/reparar")
async def reparar() -> dict[str, Any]:
    """Desactiva todos los sabotajes."""
    antes = sabotajes.activos()
    sabotajes.desactivar_todos()
    logger.warning("Sabotajes desactivados (reparar): %s", ", ".join(antes) or "ninguno")
    return _estado()


@router.post("/sabotajes/{clave}/activar")
async def activar(clave: str) -> dict[str, Any]:
    """Activa un mutante."""
    sabotajes.activar(_validar_clave(clave))
    logger.warning("Sabotaje ACTIVADO: %s", clave)
    return _estado()


@router.post("/sabotajes/{clave}/desactivar")
async def desactivar(clave: str) -> dict[str, Any]:
    """Desactiva un mutante."""
    sabotajes.desactivar(_validar_clave(clave))
    logger.warning("Sabotaje desactivado: %s", clave)
    return _estado()


Nivel = Literal["componente", "integracion", "sistema", "aceptacion"]


class EjecutarPruebasEntrada(BaseModel):
    """Niveles a ejecutar (por defecto todos). No se aceptan argumentos libres de pytest."""

    niveles: list[Nivel] | None = Field(default=None, description="Vacío = todos los niveles.")


@router.post("/pruebas", responses={409: {"description": "Ya hay una ejecución de pruebas en curso."}})
async def ejecutar_pruebas(request: Request, entrada: EjecutarPruebasEntrada | None = None) -> dict[str, Any]:
    """Ejecuta la suite con los sabotajes activos y devuelve el tablero de dominó.

    Un candado impide dos ejecuciones a la vez (cada una lanza un proceso de pytest).
    """
    candado: asyncio.Lock = request.app.state.candado_pruebas
    if candado.locked():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya hay una ejecución de pruebas en curso.")
    async with candado:
        argumentos = ["-m", " or ".join(entrada.niveles)] if entrada and entrada.niveles else []
        activos = sabotajes.activos()
        logger.warning("Ejecutando pruebas con sabotajes: %s", ", ".join(activos) or "ninguno")
        ejecucion = await asyncio.to_thread(ejecutor.ejecutar_pruebas, activos, argumentos)
    return {
        "sabotajes": ejecucion.sabotajes,
        "codigo_salida": ejecucion.codigo_salida,
        "duracion_s": ejecucion.duracion_s,
        "tablero": ejecutor.armar_tablero(ejecucion.resultados),
    }
