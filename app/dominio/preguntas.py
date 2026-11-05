"""Carga y validación de los bancos de preguntas en JSON."""

import json
from pathlib import Path

from app.dominio.modelos import Pregunta

DIRECTORIO_DATOS = Path(__file__).resolve().parents[2] / "data"
CATEGORIAS = {
    "pruebas": DIRECTORIO_DATOS / "preguntas.json",
    "cultura": DIRECTORIO_DATOS / "cultura_general.json",
}
CATEGORIA_POR_DEFECTO = "pruebas"


def cargar_preguntas(
    categoria: str = CATEGORIA_POR_DEFECTO, ruta: Path | str | None = None
) -> list[Pregunta]:
    """Lee el banco de preguntas de una categoría (o de una ruta explícita) y devuelve la lista validada.

    Lanza ValueError con un mensaje claro si la categoría no existe, si el archivo no es una lista
    o si alguna pregunta es inválida.
    """
    if ruta is None:
        if categoria not in CATEGORIAS:
            disponibles = ", ".join(sorted(CATEGORIAS))
            raise ValueError(f"Categoría '{categoria}' desconocida. Disponibles: {disponibles}.")
        ruta = CATEGORIAS[categoria]
    ruta = Path(ruta)
    with ruta.open(encoding="utf-8") as archivo:
        datos = json.load(archivo)
    if not isinstance(datos, list) or not datos:
        raise ValueError(f"{ruta.name} debe contener una lista de preguntas no vacía.")

    preguntas = []
    for numero, item in enumerate(datos, start=1):
        try:
            preguntas.append(
                Pregunta(
                    texto=item["texto"],
                    opciones=tuple(item["opciones"]),
                    correcta=int(item["correcta"]),
                    tiempo_limite=float(item.get("tiempo_limite", 20)),
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Pregunta {numero} de {ruta.name} inválida: {error}") from error
    return preguntas
