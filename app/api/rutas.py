"""Endpoints REST de las partidas."""

import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, status

from app.api.esquemas import (
    CrearPartidaEntrada,
    Error,
    EstadoJugador,
    PartidaCreada,
    ResponderEntrada,
    ResultadoRespuesta,
    UnirseEntrada,
)
from app.dominio import sabotajes
from app.dominio.gestor import GestorPartidas
from app.dominio.partida import Partida
from app.tiempo_real.conexiones import GestorConexiones

router = APIRouter(prefix="/api/partidas", tags=["partidas"])

# El PIN se valida antes de buscarlo: un formato inválido es 422 y no se repite en la respuesta (DEF-010).
Pin = Annotated[str, Path(pattern=r"^\d{6}$", description="PIN de 6 dígitos.", examples=["123456"])]

RESPUESTAS_404 = {404: {"model": Error, "description": "No existe una partida con ese PIN."}}


def obtener_gestor(request: Request) -> GestorPartidas:
    return request.app.state.gestor


def obtener_conexiones(request: Request) -> GestorConexiones:
    return request.app.state.conexiones


Gestor = Annotated[GestorPartidas, Depends(obtener_gestor)]
Conexiones = Annotated[GestorConexiones, Depends(obtener_conexiones)]


async def difundir_estado(conexiones: GestorConexiones, partida: Partida) -> None:
    """Envía el nuevo estado público a todos los sockets de la partida."""
    await conexiones.difundir(partida.pin, {"tipo": "estado", "datos": partida.estado_publico()})


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PartidaCreada)
async def crear_partida(gestor: Gestor, entrada: CrearPartidaEntrada | None = None) -> PartidaCreada:
    """Crea una partida y devuelve su PIN y el token secreto del anfitrión."""
    categoria = entrada.categoria if entrada else "pruebas"
    partida, token = gestor.crear(categoria)
    return PartidaCreada(pin=partida.pin, token_host=token, estado=partida.estado.value)


@router.get("/{pin}", responses=RESPUESTAS_404)
async def ver_partida(pin: Pin, gestor: Gestor) -> dict[str, Any]:
    """Estado público de la partida (sin la respuesta correcta mientras la pregunta está abierta)."""
    return gestor.obtener(pin).estado_publico()


@router.post(
    "/{pin}/jugadores",
    status_code=status.HTTP_201_CREATED,
    responses={**RESPUESTAS_404, 409: {"model": Error, "description": "Nombre repetido o partida iniciada."}},
)
async def unirse(pin: Pin, entrada: UnirseEntrada, gestor: Gestor, conexiones: Conexiones) -> dict[str, Any]:
    """Une un jugador a la partida (solo mientras está en LOBBY)."""
    partida = gestor.obtener(pin)
    jugador = partida.unirse(entrada.nombre)
    await difundir_estado(conexiones, partida)
    return {"nombre": jugador.nombre, "estado": partida.estado_publico()}


TokenHost = Annotated[str | None, Header(description="Token del anfitrión recibido al crear la partida.")]
RESPUESTAS_HOST = {
    **RESPUESTAS_404,
    403: {"model": Error, "description": "Falta el header X-Host-Token o no es válido."},
    409: {"model": Error, "description": "La partida no está en un estado que permita la acción."},
}


@router.post("/{pin}/iniciar", responses=RESPUESTAS_HOST)
async def iniciar(
    pin: Pin, gestor: Gestor, conexiones: Conexiones, x_host_token: TokenHost = None
) -> dict[str, Any]:
    """Inicia la partida (LOBBY → PREGUNTA). Solo el anfitrión."""
    partida = gestor.validar_host(pin, x_host_token)
    partida.iniciar()
    await difundir_estado(conexiones, partida)
    return partida.estado_publico()


@router.post("/{pin}/siguiente", responses=RESPUESTAS_HOST)
async def siguiente(
    pin: Pin, gestor: Gestor, conexiones: Conexiones, x_host_token: TokenHost = None
) -> dict[str, Any]:
    """Cierra la pregunta abierta o pasa a la siguiente / al final. Solo el anfitrión."""
    partida = gestor.validar_host(pin, x_host_token)
    partida.siguiente()
    await difundir_estado(conexiones, partida)
    return partida.estado_publico()


@router.post(
    "/{pin}/respuestas",
    response_model=ResultadoRespuesta,
    responses={
        **RESPUESTAS_404,
        409: {"model": Error, "description": "Ya respondió o no hay pregunta abierta."},
    },
)
async def responder(
    pin: Pin, entrada: ResponderEntrada, gestor: Gestor, conexiones: Conexiones
) -> ResultadoRespuesta:
    """Registra la respuesta de un jugador a la pregunta abierta y devuelve los puntos obtenidos."""
    partida = gestor.obtener(pin)
    tiempo_recibido = partida.tiempo_transcurrido()
    if sabotajes.esta_activo("respuesta_lenta"):
        await asyncio.sleep(sabotajes.RETARDO_RESPUESTA_LENTA_S)  # MUTANTE: incumple RNF-03
    puntos = partida.responder(entrada.nombre, entrada.opcion, tiempo_recibido=tiempo_recibido)
    jugador = partida.buscar_jugador(entrada.nombre)
    await difundir_estado(conexiones, partida)
    return ResultadoRespuesta(
        nombre=jugador.nombre, puntos=puntos, racha=jugador.racha, puntos_totales=jugador.puntos
    )


@router.get("/{pin}/jugadores/{nombre}", response_model=EstadoJugador, responses=RESPUESTAS_404)
async def ver_jugador(pin: Pin, nombre: str, gestor: Gestor) -> EstadoJugador:
    """Marcador y posición de un jugador."""
    partida = gestor.obtener(pin)
    jugador = partida.buscar_jugador(nombre)
    if jugador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No hay un jugador llamado '{nombre}' en la partida.")
    posicion = next(fila.posicion for fila in partida.ranking() if fila.nombre == jugador.nombre)
    return EstadoJugador(
        nombre=jugador.nombre,
        puntos=jugador.puntos,
        racha=jugador.racha,
        tiempo_total=round(jugador.tiempo_total, 3),
        posicion=posicion,
        respondio_pregunta_actual=jugador.nombre in partida.respuestas,
    )
