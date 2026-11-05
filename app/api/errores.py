"""Traducción de los errores del dominio a respuestas HTTP con {"detail": ...}."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.dominio.errores import AccesoDenegado, ErrorPartida, PartidaNoEncontrada

CODIGOS = (
    (PartidaNoEncontrada, status.HTTP_404_NOT_FOUND),
    (AccesoDenegado, status.HTTP_403_FORBIDDEN),
    (ErrorPartida, status.HTTP_409_CONFLICT),
)


def codigo_para(error: ErrorPartida) -> int:
    """Código HTTP del error: 404 si no existe, 403 si no tiene permiso, 409 si el estado no lo permite."""
    for tipo, codigo in CODIGOS:
        if isinstance(error, tipo):
            return codigo
    return status.HTTP_409_CONFLICT


async def manejar_error_partida(_request: Request, error: ErrorPartida) -> JSONResponse:
    return JSONResponse(status_code=codigo_para(error), content={"detail": str(error)})


async def manejar_validacion(_request: Request, error: RequestValidationError) -> JSONResponse:
    """422 sin repetir la entrada recibida: solo tipo, ubicación y mensaje de cada error (DEF-010)."""
    detalle = [{"type": e["type"], "loc": list(e["loc"]), "msg": e["msg"]} for e in error.errors()]
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": detalle})


def registrar_manejadores(app: FastAPI) -> None:
    """Registra los manejadores de ErrorPartida (404/403/409) y de validación (422)."""
    app.add_exception_handler(ErrorPartida, manejar_error_partida)
    app.add_exception_handler(RequestValidationError, manejar_validacion)
