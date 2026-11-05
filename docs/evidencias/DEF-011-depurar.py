"""Depuración paso a paso de calcular_puntos con una respuesta INCORRECTA y rápida (DEF-011).

Uso (desde la raíz del repo, en CMD):  set PYTHONPATH=. && python docs\\evidencias\\DEF-011-depurar.py
"""

import inspect
import sys
from pathlib import Path

from app.dominio import puntaje

LINEAS = Path(inspect.getsourcefile(puntaje)).read_text(encoding="utf-8").splitlines()


def traza(frame, evento, argumento):
    if frame.f_code.co_name == "calcular_puntos":
        if evento == "line":
            linea = LINEAS[frame.f_lineno - 1].strip()
            print(f"línea {frame.f_lineno:>3}: {linea:<60} | {dict(frame.f_locals)}")
        elif evento == "return":
            print(f"RETORNA {argumento}")
    return traza


sys.settrace(traza)
resultado = puntaje.calcular_puntos(False, 1.0, 20.0, 4)
sys.settrace(None)
print(f"\nEsperado (0, 0) para una respuesta incorrecta; obtenido {resultado}")
