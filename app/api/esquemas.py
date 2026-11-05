"""Esquemas Pydantic de entrada y salida de la API."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

# Se quitan los espacios de los extremos ANTES de validar la longitud: "   " queda vacío y es 422 (DEF-008).
Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]


class CrearPartidaEntrada(BaseModel):
    """Datos opcionales para crear una partida."""

    categoria: Literal["pruebas", "cultura"] = Field(default="pruebas", description="Banco de preguntas.")


class PartidaCreada(BaseModel):
    """Respuesta al crear una partida. El token solo lo recibe el anfitrión."""

    pin: str = Field(description="PIN de 6 dígitos para que los jugadores se unan.")
    token_host: str = Field(description="Token secreto del anfitrión (header X-Host-Token).")
    estado: str


class UnirseEntrada(BaseModel):
    """Jugador que quiere unirse a una partida."""

    nombre: Nombre = Field(description="Nombre visible, de 1 a 20 caracteres (sin contar espacios extremos).")


class ResponderEntrada(BaseModel):
    """Respuesta de un jugador a la pregunta abierta."""

    nombre: Nombre
    opcion: int = Field(ge=0, le=3, description="Índice de la opción elegida (0 a 3).")


class ResultadoRespuesta(BaseModel):
    """Puntos obtenidos con una respuesta."""

    nombre: str
    puntos: int
    racha: int
    puntos_totales: int


class EstadoJugador(BaseModel):
    """Marcador de un jugador."""

    nombre: str
    puntos: int
    racha: int
    tiempo_total: float
    posicion: int
    respondio_pregunta_actual: bool


class Error(BaseModel):
    """Formato de todos los errores de la API."""

    detail: str
