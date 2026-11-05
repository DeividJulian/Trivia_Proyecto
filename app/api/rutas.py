"""Endpoints REST de las partidas."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Request, status

from app.api.esquemas import CrearPartidaEntrada, Error, PartidaCreada, UnirseEntrada
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


@router.post(
    "/{pin}/jugadores",
    status_code=status.HTTP_201_CREATED,
    responses={**RESPUESTAS_404, 409: {"model": Error, "description": "Nombre repetido o partida iniciada."}},
)
async def unirse(pin: str, entrada: UnirseEntrada, gestor: Gestor) -> dict[str, Any]:
    """Une un jugador a la partida (solo mientras está en LOBBY)."""
    partida = gestor.obtener(pin)
    jugador = partida.unirse(entrada.nombre)
    return {"nombre": jugador.nombre, "estado": partida.estado_publico()}


TokenHost = Annotated[str | None, Header(description="Token del anfitrión recibido al crear la partida.")]
RESPUESTAS_HOST = {
    **RESPUESTAS_404,
    403: {"model": Error, "description": "Falta el header X-Host-Token o no es válido."},
    409: {"model": Error, "description": "La partida no está en un estado que permita la acción."},
}


@router.post("/{pin}/iniciar", responses=RESPUESTAS_HOST)
async def iniciar(pin: str, gestor: Gestor, x_host_token: TokenHost = None) -> dict[str, Any]:
    """Inicia la partida (LOBBY → PREGUNTA). Solo el anfitrión."""
    partida = gestor.validar_host(pin, x_host_token)
    partida.iniciar()
    return partida.estado_publico()


@router.post("/{pin}/siguiente", responses=RESPUESTAS_HOST)
async def siguiente(pin: str, gestor: Gestor, x_host_token: TokenHost = None) -> dict[str, Any]:
    """Cierra la pregunta abierta o pasa a la siguiente / al final. Solo el anfitrión."""
    partida = gestor.validar_host(pin, x_host_token)
    partida.siguiente()
    return partida.estado_publico()
