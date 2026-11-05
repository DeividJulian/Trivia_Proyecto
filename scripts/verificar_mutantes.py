"""Verifica que la suite de pruebas detecta (mata) a cada mutante del Saboteador.

Por cada sabotaje del catálogo ejecuta pytest con SABOTAJES=<clave>:
  - DETECTADO  si al menos una prueba falla (el mutante muere).
  - SOBREVIVIO si todas pasan: las pruebas no ven ese error -> hay que escribir una prueba nueva.

Se excluyen las pruebas marcadas "sabotajes" (las que comprueban la conexión de cada mutante):
la detección tiene que venir de las pruebas reales del juego.

Uso (CMD de Windows):  python scripts\\verificar_mutantes.py [clave ...]
Termina con código 1 si algún mutante sobrevive. Solo usa caracteres ASCII en la salida.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.dominio.sabotajes import CATALOGO  # noqa: E402 - necesita RAIZ en sys.path

# Primero los niveles rápidos: con -x pytest se detiene en el primer fallo.
ORDEN_NIVELES = ["tests/componente", "tests/integracion", "tests/sistema", "tests/aceptacion"]


def probar_mutante(clave: str) -> tuple[bool, float, str]:
    """Ejecuta la suite con el mutante activo. Devuelve (detectado, segundos, primera prueba que falló)."""
    comando = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", "-m", "not sabotajes"]
    inicio = time.perf_counter()
    proceso = subprocess.run(  # noqa: S603 - ejecuta pytest con argumentos propios, sin shell
        [*comando, *ORDEN_NIVELES],
        cwd=RAIZ,
        env={**os.environ, "SABOTAJES": clave},
        capture_output=True,
        text=True,
        check=False,
    )
    duracion = time.perf_counter() - inicio
    primera = next((linea for linea in proceso.stdout.splitlines() if linea.startswith("FAILED")), "")
    return proceso.returncode != 0, duracion, primera.removeprefix("FAILED ").split(" - ")[0]


def main() -> int:
    claves = sys.argv[1:] or list(CATALOGO)
    desconocidas = [c for c in claves if c not in CATALOGO]
    if desconocidas:
        print(f"Sabotajes desconocidos: {', '.join(desconocidas)}")
        return 2

    print(f"Verificando {len(claves)} mutantes (SABOTAJES=<clave> pytest -x -m 'not sabotajes')\n")
    sobrevivientes = []
    for clave in claves:
        detectado, segundos, prueba = probar_mutante(clave)
        estado = "DETECTADO " if detectado else "SOBREVIVIO"
        print(f"  [{estado}] {clave:<22} {segundos:6.1f} s  {prueba}")
        if not detectado:
            sobrevivientes.append(clave)

    detectados = len(claves) - len(sobrevivientes)
    porcentaje = 100 * detectados / len(claves)
    print(f"\nMutantes detectados: {detectados}/{len(claves)} ({porcentaje:.0f} %)  -  RNF-07 exige 100 %")
    if sobrevivientes:
        print("Sobrevivieron: " + ", ".join(sobrevivientes) + "  -> escribir pruebas que los detecten.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
