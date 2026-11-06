"""Muestrea la CPU del generador de carga (Locust), del servidor y del sistema durante una prueba.

Sirve para saber desde cuántos usuarios los datos dejan de ser fiables: si Locust satura su núcleo,
parte de la latencia medida es del propio generador y no del servidor.

Uso (CMD, en otra terminal, antes de lanzar Locust; se detiene con Ctrl+C o con --duracion):
  python performance\\monitor_cpu.py performance\\resultados\\quiebre_local_cpu.csv
  python performance\\monitor_cpu.py performance\\resultados\\quiebre_docker_cpu.csv ^
         --contenedor testquiz-carga

CPU en % de UN núcleo (como el Administrador de tareas por proceso): Locust usa un solo núcleo,
así que se satura cerca del 100 %. Con --contenedor, la CPU del servidor sale de `docker stats`.
"""

import argparse
import bisect
import csv
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psutil

# psutil se importa dentro de las funciones que lo usan: la imagen Docker copia performance/ y
# corre sus pruebas sin tener psutil instalado (ver DEF-017 y DEF-026).

UMBRAL_SATURACION_PCT = 90.0  # el mismo aviso que da Locust ("CPU usage above 90%")


def porcentaje_docker(texto: str) -> float | None:
    """'123.45%' -> 123.45; None si docker no devolvió un valor."""
    limpio = texto.strip().removesuffix("%").strip()
    try:
        return float(limpio)
    except ValueError:
        return None


def es_proceso(cmdline: list[str], patron: str) -> bool:
    """True si algún argumento del proceso contiene el patrón (sin distinguir mayúsculas)."""
    patron = patron.casefold()
    return any(patron in Path(arg).name.casefold() or patron in arg.casefold() for arg in cmdline)


def usuarios_en(momento: float, historial: list[tuple[float, int]]) -> int:
    """Usuarios activos en un instante, según el historial de Locust ordenado [(timestamp, usuarios)]."""
    if not historial:
        return 0
    marcas = [t for t, _ in historial]
    indice = bisect.bisect_right(marcas, momento) - 1
    return historial[indice][1] if indice >= 0 else 0


def cpu_por_escalon(
    muestras: list[dict[str, float]], historial: list[tuple[float, int]]
) -> dict[int, dict[str, float]]:
    """Máximo y media de CPU del generador y del servidor para cada número de usuarios."""
    grupos: dict[int, list[dict[str, float]]] = {}
    for muestra in muestras:
        usuarios = usuarios_en(muestra["t"], historial)
        if usuarios > 0:
            grupos.setdefault(usuarios, []).append(muestra)
    resultado = {}
    for usuarios, grupo in sorted(grupos.items()):
        generador = [m["generador"] for m in grupo]
        servidor = [m["servidor"] for m in grupo if m["servidor"] >= 0]
        resultado[usuarios] = {
            "generador_max": max(generador),
            "generador_media": round(sum(generador) / len(generador), 1),
            "servidor_max": max(servidor) if servidor else -1.0,
            "saturado": max(generador) >= UMBRAL_SATURACION_PCT,
        }
    return resultado


def leer_muestras(ruta: Path) -> list[dict[str, float]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return [{k: float(v) for k, v in fila.items()} for fila in csv.DictReader(archivo)]


def _procesos(patron: str) -> list["psutil.Process"]:
    import psutil

    encontrados = []
    for proceso in psutil.process_iter(["cmdline"]):
        try:
            if proceso.pid != psutil.Process().pid and es_proceso(proceso.info["cmdline"] or [], patron):
                encontrados.append(proceso)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return encontrados


def _cpu(procesos: list["psutil.Process"]) -> float:
    import psutil

    total = 0.0
    for proceso in procesos:
        try:
            total += proceso.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return total


def _cpu_contenedor(nombre: str) -> float:
    docker = shutil.which("docker")
    if docker is None:
        return -1.0
    salida = subprocess.run(  # noqa: S603 - comando fijo de docker, sin shell
        [docker, "stats", "--no-stream", "--format", "{{.CPUPerc}}", nombre],
        capture_output=True,
        text=True,
        check=False,
    )
    valor = porcentaje_docker(salida.stdout)
    return -1.0 if valor is None else valor


def main() -> int:
    import psutil

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("salida", type=Path)
    parser.add_argument("--contenedor", help="nombre del contenedor del servidor (en vez de uvicorn local)")
    parser.add_argument("--intervalo", type=float, default=2.0)
    parser.add_argument("--duracion", type=float, default=0.0, help="segundos (0 = hasta Ctrl+C)")
    argumentos = parser.parse_args()

    argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
    psutil.cpu_percent(None)
    fin = time.time() + argumentos.duracion if argumentos.duracion else None
    with argumentos.salida.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["t", "generador", "servidor", "sistema"])
        locust: list[psutil.Process] = []
        uvicorn: list[psutil.Process] = []
        try:
            while fin is None or time.time() < fin:
                if not locust:
                    locust = _procesos("locust")
                    _cpu(locust)  # la primera lectura de psutil siempre es 0
                if not argumentos.contenedor and not uvicorn:
                    uvicorn = _procesos("uvicorn")
                    _cpu(uvicorn)
                time.sleep(argumentos.intervalo)
                servidor = _cpu_contenedor(argumentos.contenedor) if argumentos.contenedor else _cpu(uvicorn)
                escritor.writerow(
                    [
                        f"{time.time():.1f}",
                        f"{_cpu(locust):.1f}",
                        f"{servidor:.1f}",
                        f"{psutil.cpu_percent(None):.1f}",
                    ]
                )
                archivo.flush()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
