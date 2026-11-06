"""Ejecuta la suite de pruebas con sabotajes activos y arma el "tablero de dominó".

- Un módulo está CAÍDO si tiene al menos una prueba que falla.
- Un módulo está EN RIESGO si no falla, pero depende (según el mapa de impacto) de uno caído.
- En cualquier otro caso está OK.
"""

import os
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.calidad.impacto import modulos_afectados

RAIZ = Path(__file__).resolve().parents[2]

# marcador de pytest -> módulo del mapa de impacto
MODULO_DE_MARCADOR = {
    "puntaje": "Puntaje",
    "ranking": "Ranking",
    "partida": "Partida",
    "gestor": "Gestor",
    "api": "API",
    "preguntas": "Preguntas",
}

CAIDO, EN_RIESGO, OK = "CAIDO", "EN_RIESGO", "OK"


@dataclass(frozen=True)
class ResultadoPrueba:
    nombre: str
    modulos: tuple[str, ...]
    nivel: str
    fallo: bool
    mensaje: str = ""


@dataclass
class Ejecucion:
    sabotajes: list[str]
    codigo_salida: int
    duracion_s: float
    resultados: list[ResultadoPrueba] = field(default_factory=list)


def leer_junit(ruta: Path) -> list[ResultadoPrueba]:
    """Lee el JUnit XML de pytest (con las propiedades módulo y nivel que agrega el conftest)."""
    raiz = ET.parse(ruta).getroot()  # noqa: S314 - XML generado localmente por pytest, no es entrada externa
    resultados = []
    for caso in raiz.iter("testcase"):
        propiedades = [(p.get("name"), p.get("value")) for p in caso.iter("property")]
        modulos = tuple(
            MODULO_DE_MARCADOR[valor]
            for nombre, valor in propiedades
            if nombre == "modulo" and valor in MODULO_DE_MARCADOR
        )
        nivel = next((valor for nombre, valor in propiedades if nombre == "nivel"), "")
        error = caso.find("failure")
        if error is None:
            error = caso.find("error")
        resultados.append(
            ResultadoPrueba(
                nombre=f"{caso.get('classname')}::{caso.get('name')}",
                modulos=modulos,
                nivel=nivel or "",
                fallo=error is not None,
                mensaje=(error.get("message") or "")[:200] if error is not None else "",
            )
        )
    return resultados


def armar_tablero(resultados: list[ResultadoPrueba]) -> dict[str, Any]:
    """Estado de cada módulo: CAIDO, EN_RIESGO u OK, con sus pruebas fallidas."""
    modulos: dict[str, dict[str, Any]] = {
        modulo: {"estado": OK, "total": 0, "fallidas": [], "en_riesgo_por": []}
        for modulo in MODULO_DE_MARCADOR.values()
    }
    for resultado in resultados:
        for modulo in resultado.modulos:
            modulos[modulo]["total"] += 1
            if resultado.fallo:
                modulos[modulo]["fallidas"].append(resultado.nombre)

    caidos = sorted(m for m, datos in modulos.items() if datos["fallidas"])
    for modulo in caidos:
        modulos[modulo]["estado"] = CAIDO
    for caido in caidos:
        for afectado in sorted(modulos_afectados(caido)):
            datos = modulos.get(afectado)
            if datos is not None and datos["estado"] != CAIDO:
                datos["estado"] = EN_RIESGO
                datos["en_riesgo_por"].append(caido)

    fallidas = [r for r in resultados if r.fallo]
    return {
        "resumen": {
            "pruebas": len(resultados),
            "fallidas": len(fallidas),
            "caidos": caidos,
            "en_riesgo": sorted(m for m, d in modulos.items() if d["estado"] == EN_RIESGO),
            "por_nivel": _fallidas_por_nivel(fallidas),
        },
        "modulos": modulos,
    }


def _fallidas_por_nivel(fallidas: list[ResultadoPrueba]) -> dict[str, int]:
    conteo: dict[str, int] = {}
    for resultado in fallidas:
        clave = resultado.nivel or "sin_nivel"
        conteo[clave] = conteo.get(clave, 0) + 1
    return conteo


def ejecutar_pruebas(
    sabotajes: list[str], argumentos: list[str] | None = None, timeout_s: int = 600
) -> Ejecucion:
    """Ejecuta pytest en otro proceso con SABOTAJES=<claves> y devuelve los resultados."""
    with tempfile.TemporaryDirectory() as carpeta:
        junit = Path(carpeta) / "resultado.xml"
        comando = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"]
        entorno = {**os.environ, "SABOTAJES": ",".join(sabotajes)}
        inicio = time.perf_counter()
        proceso = subprocess.run(  # noqa: S603 - ejecuta pytest con argumentos propios, sin shell
            [*comando, *(argumentos or [])],
            cwd=RAIZ,
            env=entorno,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        duracion = time.perf_counter() - inicio
        resultados = leer_junit(junit) if junit.exists() else []
    return Ejecucion(sabotajes, proceso.returncode, round(duracion, 2), resultados)
