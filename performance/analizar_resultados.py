"""Analiza el historial de Locust: gráfica (usuarios vs p95 y % de fallos) y reporte en Markdown.

Uso (CMD):  python performance\\analizar_resultados.py quiebre_local
Lee   performance\\resultados\\quiebre_local_stats_history.csv  (locust --csv-full-history)
Crea  performance\\resultados\\quiebre_local_grafica.png  y  quiebre_local_reporte.md

  - Punto de degradación: primer escalón que incumple RNF-01 (p95 >= 500 ms) o RNF-02 (fallos >= 1 %).
  - Punto de quiebre: primer escalón con más del 5 % de fallos o p95 mayor a 2000 ms.
"""

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verificar_umbrales import FALLOS_MAX_PCT, P95_MAX_MS, supera_quiebre  # noqa: E402 - mismo directorio

RESULTADOS = Path(__file__).resolve().parent / "resultados"


@dataclass(frozen=True)
class Escalon:
    usuarios: int
    peticiones: int
    fallos_pct: float
    p95_ms: float
    rps: float

    @property
    def degradado(self) -> bool:
        return self.p95_ms >= P95_MAX_MS or self.fallos_pct >= FALLOS_MAX_PCT

    @property
    def quebrado(self) -> bool:
        return supera_quiebre(self.fallos_pct, self.p95_ms)


def _numero(texto: str) -> float | None:
    try:
        return float(texto)
    except ValueError:  # "N/A" cuando aún no hay peticiones
        return None


def leer_historial(ruta: Path) -> list[dict[str, str]]:
    """Filas "Aggregated" del historial, con usuarios > 0."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return [f for f in csv.DictReader(archivo) if f["Name"] == "Aggregated" and int(f["User Count"]) > 0]


def agrupar_escalones(filas: list[dict[str, str]]) -> list[Escalon]:
    """Agrupa las filas consecutivas con el mismo número de usuarios.

    p95 del escalón = el mayor p95 de su ventana (criterio conservador); fallos = fallos nuevos del
    escalón / peticiones nuevas del escalón.
    """
    escalones: list[Escalon] = []
    peticiones_previas = fallos_previos = 0
    grupo: list[dict[str, str]] = []

    def cerrar() -> None:
        nonlocal peticiones_previas, fallos_previos
        if not grupo:
            return
        ultima = grupo[-1]
        peticiones = int(ultima["Total Request Count"]) - peticiones_previas
        fallos = int(ultima["Total Failure Count"]) - fallos_previos
        p95s = [v for v in (_numero(f["95%"]) for f in grupo) if v is not None]
        rps = [v for v in (_numero(f["Requests/s"]) for f in grupo) if v is not None]
        escalones.append(
            Escalon(
                usuarios=int(ultima["User Count"]),
                peticiones=peticiones,
                fallos_pct=round(100.0 * fallos / peticiones, 2) if peticiones else 0.0,
                p95_ms=max(p95s) if p95s else 0.0,
                rps=round(sum(rps) / len(rps), 1) if rps else 0.0,
            )
        )
        peticiones_previas = int(ultima["Total Request Count"])
        fallos_previos = int(ultima["Total Failure Count"])

    for fila in filas:
        if grupo and fila["User Count"] != grupo[-1]["User Count"]:
            cerrar()
            grupo = []
        grupo.append(fila)
    cerrar()
    return escalones


def puntos_criticos(escalones: list[Escalon]) -> tuple[Escalon | None, Escalon | None]:
    """(punto de degradación, punto de quiebre); None si no se alcanzó."""
    degradacion = next((e for e in escalones if e.degradado), None)
    quiebre = next((e for e in escalones if e.quebrado), None)
    return degradacion, quiebre


def graficar(escalones: list[Escalon], destino: Path, titulo: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    usuarios = [e.usuarios for e in escalones]
    figura, eje_p95 = plt.subplots(figsize=(9, 5))
    eje_p95.plot(usuarios, [e.p95_ms for e in escalones], marker="o", color="#1f77b4", label="p95 (ms)")
    eje_p95.axhline(P95_MAX_MS, color="#1f77b4", linestyle=":", label="RNF-01: 500 ms")
    eje_p95.set_xlabel("Usuarios concurrentes")
    eje_p95.set_ylabel("p95 (ms)", color="#1f77b4")
    eje_fallos = eje_p95.twinx()
    eje_fallos.plot(
        usuarios, [e.fallos_pct for e in escalones], marker="s", color="#d62728", label="Fallos (%)"
    )
    eje_fallos.axhline(5.0, color="#d62728", linestyle=":", label="Quiebre: 5 %")
    eje_fallos.set_ylabel("Fallos (%)", color="#d62728")
    lineas = eje_p95.get_legend_handles_labels()[0] + eje_fallos.get_legend_handles_labels()[0]
    eje_p95.legend(lineas, [linea.get_label() for linea in lineas], loc="upper left")
    eje_p95.set_title(titulo)
    eje_p95.grid(alpha=0.3)
    figura.tight_layout()
    figura.savefig(destino, dpi=120)
    plt.close(figura)


def reporte(prefijo: str, escalones: list[Escalon]) -> str:
    degradacion, quiebre = puntos_criticos(escalones)
    maximo = escalones[-1].usuarios if escalones else 0
    lineas = [
        f"# Resultados de rendimiento – {prefijo}",
        "",
        f"![Usuarios vs p95 y fallos]({prefijo}_grafica.png)",
        "",
        "| Usuarios | Peticiones | p95 (ms) | Fallos (%) | Peticiones/s | Estado |",
        "|---|---|---|---|---|---|",
    ]
    for e in escalones:
        estado = "QUIEBRE" if e.quebrado else "DEGRADADO" if e.degradado else "OK"
        lineas.append(
            f"| {e.usuarios} | {e.peticiones} | {e.p95_ms:.0f} | {e.fallos_pct:.2f} | {e.rps} | {estado} |"
        )
    lineas += [
        "",
        "- **Punto de degradación** (incumple RNF-01 o RNF-02): "
        + (f"{degradacion.usuarios} usuarios" if degradacion else f"no se alcanzó hasta {maximo} usuarios"),
        "- **Punto de quiebre** (> 5 % de fallos o p95 > 2000 ms): "
        + (f"{quiebre.usuarios} usuarios" if quiebre else f"no se alcanzó hasta {maximo} usuarios"),
        "",
    ]
    return "\n".join(lineas)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    prefijo = sys.argv[1]
    historial = RESULTADOS / f"{prefijo}_stats_history.csv"
    escalones = agrupar_escalones(leer_historial(historial))
    if not escalones:
        print(f"{historial.name} no tiene datos.")
        return 1
    graficar(escalones, RESULTADOS / f"{prefijo}_grafica.png", f"Punto de quiebre – {prefijo}")
    texto = reporte(prefijo, escalones)
    (RESULTADOS / f"{prefijo}_reporte.md").write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
