"""Modo Saboteador: mutantes controlados.

Cada sabotaje es un "mutante": una rama alternativa del código que solo se ejecuta si
esta_activo("clave") es verdadero. El código nunca se modifica en caliente.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Sabotaje:
    """Descripción de un mutante y del nivel de prueba que debería detectarlo."""

    clave: str
    nombre: str
    modulo: str
    descripcion: str
    nivel_que_lo_detecta: str


CATALOGO: dict[str, Sabotaje] = {}


def _registrar(sabotaje: Sabotaje) -> None:
    CATALOGO[sabotaje.clave] = sabotaje


# --- Catálogo de mutantes ----------------------------------------------------------------------


_registrar(
    Sabotaje(
        clave="tiempo_estricto",
        nombre="Tiempo estricto",
        modulo="puntaje",
        descripcion="es_respuesta_a_tiempo usa < en vez de <=: responder justo en el límite deja de contar.",
        nivel_que_lo_detecta="componente (valores límite) y sistema (extremo a extremo)",
    )
)

_registrar(
    Sabotaje(
        clave="racha_no_suma",
        nombre="Racha que no suma",
        modulo="puntaje",
        descripcion="sumar_racha no aumenta la racha al acertar: nunca hay bono de racha.",
        nivel_que_lo_detecta="componente (racha) e integración (puntaje + racha + ranking)",
    )
)

_registrar(
    Sabotaje(
        clave="bono_sin_acierto",
        nombre="Bono sin acierto",
        modulo="puntaje",
        descripcion="Reproduce el error de la v2: una respuesta incorrecta recibe el bono por velocidad.",
        nivel_que_lo_detecta="componente, sistema (extremo a extremo) y aceptación (HU-02)",
    )
)

# --- Estado: qué sabotajes están activos -------------------------------------------------------

_activos: set[str] = set()


def _validar(clave: str) -> str:
    if clave not in CATALOGO:
        disponibles = ", ".join(sorted(CATALOGO)) or "ninguno"
        raise KeyError(f"Sabotaje desconocido: '{clave}'. Disponibles: {disponibles}.")
    return clave


def esta_activo(clave: str) -> bool:
    """True si el mutante indicado está activo."""
    return clave in _activos


def activar(clave: str) -> None:
    _activos.add(_validar(clave))


def desactivar(clave: str) -> None:
    _activos.discard(_validar(clave))


def desactivar_todos() -> None:
    _activos.clear()


def activos() -> list[str]:
    """Claves de los sabotajes activos, ordenadas."""
    return sorted(_activos)


def leer_activos_del_entorno(valor: str | None = None) -> list[str]:
    """Activa los sabotajes listados en la variable SABOTAJES (separados por comas).

    Lo usa verificar_mutantes.py para ejecutar la suite con un mutante activo.
    """
    texto = os.environ.get("SABOTAJES", "") if valor is None else valor
    claves = [clave.strip() for clave in texto.split(",") if clave.strip()]
    for clave in claves:
        activar(clave)
    return claves


leer_activos_del_entorno()
