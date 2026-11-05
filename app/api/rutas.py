"""Endpoints REST de las partidas."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status

from app.api.esquemas import CrearPartidaEntrada, Error, PartidaCreada
from app.dominio.gestor import GestorPartidas

router = APIRouter(prefix="/api/partidas", tags=["partidas"])

RESPUESTAS_404 = {404: {"model": Error, "description": "No existe una partida con ese PIN."}}


def obtener_gestor(request: Request) -> GestorPartidas:
    return request.app.state.gestor


Gestor = Annotated[GestorPartidas, Depends(obtener_gestor)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PartidaCreada)
async def crear_partida(gestor: Gestor, entrada: CrearPartidaEntrada | None = None) -> PartidaCreada:
    """Crea una partida y devuelve su PIN y el token secreto del anfitrión."""
    categoria = entrada.categoria if entrada else "pruebas"
    partida, token = gestor.crear(categoria)
    return PartidaCreada(pin=partida.pin, token_host=token, estado=partida.estado.value)


@router.get("/{pin}", responses=RESPUESTAS_404)
async def ver_partida(pin: str, gestor: Gestor) -> dict[str, Any]:
    """Estado público de la partida (sin la respuesta correcta mientras la pregunta está abierta)."""
    return gestor.obtener(pin).estado_publico()
