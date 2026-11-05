"""Regresión selectiva por análisis de impacto.

Lee los archivos cambiados respecto de una rama base (por defecto develop), deduce los módulos
afectados con app/calidad/impacto.py y ejecuta pytest solo con los marcadores necesarios.

Uso (CMD de Windows, desde la raíz del repo):
    python scripts\\regresion_por_impacto.py               ejecuta la regresión
    python scripts\\regresion_por_impacto.py --solo-ver    muestra el plan sin ejecutar
    python scripts\\regresion_por_impacto.py --base main   compara contra otra rama
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.calidad.impacto import planificar_regresion  # noqa: E402 - necesita RAIZ en sys.path


def archivos_cambiados(base: str) -> list[str]:
    """Archivos que difieren de la rama base (commits de la rama + cambios sin commit)."""
    git = shutil.which("git")
    if git is None:
        raise SystemExit("No se encontró git en el PATH.")
    salida = subprocess.run(  # noqa: S603 - comando fijo, sin shell; base es un nombre de rama de git
        [git, "diff", "--name-only", base],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=True,
    )
    return [linea for linea in salida.stdout.splitlines() if linea.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Regresión selectiva por análisis de impacto.")
    parser.add_argument("--base", default="develop", help="Rama contra la que se compara (develop).")
    parser.add_argument("--solo-ver", action="store_true", help="Solo muestra el plan.")
    args = parser.parse_args()

    archivos = archivos_cambiados(args.base)
    plan = planificar_regresion(archivos)
    print(f"Archivos cambiados respecto de {args.base}: {len(archivos)}")
    for archivo in archivos:
        print(f"  - {archivo}")
    print(f"Plan: {plan.motivo}")

    argumentos = plan.argumentos_pytest()
    if not argumentos:
        print("No hay pruebas que ejecutar.")
        return 0
    comando = [sys.executable, "-m", "pytest", *argumentos]
    print("Comando: pytest " + " ".join(f'"{a}"' if " " in a else a for a in argumentos))
    if args.solo_ver:
        return 0
    return subprocess.call(comando, cwd=RAIZ)  # noqa: S603 - ejecuta pytest con argumentos propios


if __name__ == "__main__":
    raise SystemExit(main())
