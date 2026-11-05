"""Verifica RNF-01 y RNF-02 sobre el CSV de estadísticas de Locust.

  RNF-01: p95 < 500 ms con 50 usuarios.
  RNF-02: menos del 1 % de peticiones fallidas.

Uso (CMD):  python performance\\verificar_umbrales.py performance\\resultados\\carga_local_stats.csv
Termina con código 1 si no se cumple algún umbral. Los umbrales NO se cambian para que algo pase:
si no se cumplen, se registra un defecto no funcional.
"""

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

P95_MAX_MS = 500.0  # RNF-01
FALLOS_MAX_PCT = 1.0  # RNF-02


@dataclass(frozen=True)
class Resumen:
    peticiones: int
    fallos: int
    p95_ms: float
    mediana_ms: float
    rps: float

    @property
    def fallos_pct(self) -> float:
        return 100.0 * self.fallos / self.peticiones if self.peticiones else 0.0


def leer_agregado(ruta: Path) -> Resumen:
    """Lee la fila "Aggregated" del archivo *_stats.csv de Locust."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            if fila["Name"] == "Aggregated":
                return Resumen(
                    peticiones=int(fila["Request Count"]),
                    fallos=int(fila["Failure Count"]),
                    p95_ms=float(fila["95%"]),
                    mediana_ms=float(fila["Median Response Time"]),
                    rps=float(fila["Requests/s"]),
                )
    raise ValueError(f"{ruta.name} no tiene la fila 'Aggregated'.")


def evaluar(resumen: Resumen) -> list[tuple[str, str, str, bool]]:
    """Devuelve (requisito, medido, umbral, cumple) para cada RNF."""
    return [
        ("RNF-01 p95", f"{resumen.p95_ms:.0f} ms", f"< {P95_MAX_MS:.0f} ms", resumen.p95_ms < P95_MAX_MS),
        (
            "RNF-02 fallos",
            f"{resumen.fallos_pct:.2f} %",
            f"< {FALLOS_MAX_PCT:.0f} %",
            resumen.fallos_pct < FALLOS_MAX_PCT,
        ),
    ]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    resumen = leer_agregado(Path(sys.argv[1]))
    if resumen.peticiones == 0:
        print("El CSV no tiene peticiones: la prueba de carga no se ejecutó.")
        return 1
    print(
        f"Peticiones: {resumen.peticiones}  fallos: {resumen.fallos}  "
        f"mediana: {resumen.mediana_ms:.0f} ms  rps: {resumen.rps:.1f}"
    )
    resultados = evaluar(resumen)
    for requisito, medido, umbral, cumple in resultados:
        estado = "CUMPLE   " if cumple else "NO CUMPLE"
        print(f"  [{estado}] {requisito:<14} medido {medido:>9}  umbral {umbral}")
    return 0 if all(cumple for *_, cumple in resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
