"""Compara escenarios de carga (REST vs. REST + WebSocket, uvicorn local vs. contenedor).

Uso (CMD):
  python performance\\comparar_escenarios.py quiebre comparacion_quiebre ^
         quiebre_rest_local="REST · uvicorn" quiebre_ws_local="REST+WS · uvicorn" ...
  python performance\\comparar_escenarios.py carga comparacion_carga carga_rest_local="REST · uvicorn" ...

Para cada prefijo lee de performance\\resultados\\:
  <prefijo>_stats.csv / <prefijo>_stats_history.csv   (Locust; solo peticiones REST)
  <prefijo>_cpu.csv                                    (monitor_cpu.py, opcional)
  <prefijo>_ws_eventos.csv                             (locustfile_ws.py, opcional)
Crea <salida>.md y, en modo quiebre, <salida>.png.

Un escalón es "no fiable" si la CPU del generador (Locust) llegó al 90 % de su núcleo: desde ahí
parte de la latencia medida la pone el propio generador, no el servidor.
"""

import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analizar_resultados import Escalon, agrupar_escalones, leer_historial  # noqa: E402
from medidor_ws import leer_eventos, por_escalon, resumir  # noqa: E402
from monitor_cpu import UMBRAL_SATURACION_PCT, cpu_por_escalon, leer_muestras  # noqa: E402
from verificar_umbrales import leer_agregado  # noqa: E402

RESULTADOS = Path(__file__).resolve().parent / "resultados"
COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]  # paleta categórica en orden fijo


@dataclass
class FilaEscalon:
    usuarios: int
    escalon: Escalon
    cpu: dict[str, float] = field(default_factory=dict)
    ws: dict[str, Any] = field(default_factory=dict)

    @property
    def fiable(self) -> bool:
        return not self.cpu or self.cpu["generador_max"] < UMBRAL_SATURACION_PCT


def marcas_de_tiempo(ruta: Path) -> list[tuple[float, int]]:
    """[(timestamp, usuarios)] de las filas Aggregated del historial de Locust."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return [
            (float(f["Timestamp"]), int(f["User Count"]))
            for f in csv.DictReader(archivo)
            if f["Name"] == "Aggregated"
        ]


def unir_escalones(
    escalones: list[Escalon], cpu: dict[int, dict[str, float]], ws: list[dict[str, Any]]
) -> list[FilaEscalon]:
    ws_por_usuarios = {fila["usuarios"]: fila for fila in ws}
    return [
        FilaEscalon(e.usuarios, e, cpu.get(e.usuarios, {}), ws_por_usuarios.get(e.usuarios, {}))
        for e in escalones
    ]


def primer_no_fiable(filas: list[FilaEscalon]) -> int | None:
    return next((f.usuarios for f in filas if not f.fiable), None)


def _texto(valor: float | None, formato: str = "{:.0f}") -> str:
    return "—" if valor is None or valor < 0 else formato.format(valor)


def cargar_quiebre(prefijo: str) -> list[FilaEscalon]:
    historial = RESULTADOS / f"{prefijo}_stats_history.csv"
    escalones = agrupar_escalones(leer_historial(historial))
    ruta_cpu = RESULTADOS / f"{prefijo}_cpu.csv"
    cpu = cpu_por_escalon(leer_muestras(ruta_cpu), marcas_de_tiempo(historial)) if ruta_cpu.exists() else {}
    ruta_ws = RESULTADOS / f"{prefijo}_ws_eventos.csv"
    ws = por_escalon(leer_eventos(ruta_ws)) if ruta_ws.exists() else []
    return unir_escalones(escalones, cpu, ws)


def fila_md(celdas: list[str]) -> str:
    return "| " + " | ".join(celdas) + " |"


COLUMNAS_QUIEBRE = [
    "Usuarios",
    "p95 REST (ms)",
    "Fallos (%)",
    "Peticiones/s",
    "CPU Locust máx. (%)",
    "CPU servidor máx. (%)",
    "WS mensajes/s",
    "WS difusión p95 (ms)",
    "¿Fiable?",
]


def tabla_quiebre(etiqueta: str, filas: list[FilaEscalon]) -> str:
    lineas = [f"### {etiqueta}", "", fila_md(COLUMNAS_QUIEBRE), fila_md(["---"] * len(COLUMNAS_QUIEBRE))]
    for f in filas:
        e = f.escalon
        lineas.append(
            fila_md(
                [
                    str(f.usuarios),
                    f"{e.p95_ms:.0f}",
                    f"{e.fallos_pct:.2f}",
                    f"{e.rps:.0f}",
                    _texto(f.cpu.get("generador_max")),
                    _texto(f.cpu.get("servidor_max")),
                    _texto(f.ws.get("mensajes_por_s")),
                    _texto(f.ws.get("latencia_p95_ms")),
                    "sí" if f.fiable else "**no**",
                ]
            )
        )
    lineas += ["", conclusion_fiabilidad(filas)]
    return "\n".join(lineas)


def conclusion_fiabilidad(filas: list[FilaEscalon]) -> str:
    corte = primer_no_fiable(filas)
    if corte is None:
        return "Locust no saturó su núcleo en ningún escalón: todos los datos son del servidor."
    fiables = [f.usuarios for f in filas if f.usuarios < corte]
    hasta = max(fiables, default=0)
    return f"Datos fiables hasta {hasta} usuarios; desde {corte} usuarios Locust saturó su núcleo."


def graficar_quiebre(series: list[tuple[str, list[FilaEscalon]]], destino: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figura, (eje_p95, eje_cpu) = plt.subplots(1, 2, figsize=(13, 5))
    for color, (etiqueta, filas) in zip(COLORES, series, strict=False):
        usuarios = [f.usuarios for f in filas]
        eje_p95.plot(
            usuarios,
            [f.escalon.p95_ms for f in filas],
            color=color,
            linewidth=2,
            marker="o",
            markersize=4,
            label=etiqueta,
        )
        con_cpu = [f for f in filas if f.cpu]
        if con_cpu:
            eje_cpu.plot(
                [f.usuarios for f in con_cpu],
                [f.cpu["generador_max"] for f in con_cpu],
                color=color,
                linewidth=2,
                marker="o",
                markersize=4,
                label=etiqueta,
            )
    eje_p95.axhline(500, color="#52514e", linewidth=1, linestyle="--")
    eje_p95.text(eje_p95.get_xlim()[0], 510, " RNF-01: p95 < 500 ms", color="#52514e", fontsize=9)
    eje_p95.set(title="p95 de las peticiones REST", xlabel="Usuarios", ylabel="p95 (ms)")
    eje_cpu.axhline(UMBRAL_SATURACION_PCT, color="#d03b3b", linewidth=1, linestyle="--")
    eje_cpu.text(
        eje_cpu.get_xlim()[0],
        UMBRAL_SATURACION_PCT + 2,
        " 90 %: el generador deja de ser fiable",
        color="#d03b3b",
        fontsize=9,
    )
    eje_cpu.set(title="CPU del generador (Locust, % de un núcleo)", xlabel="Usuarios", ylabel="CPU (%)")
    for eje in (eje_p95, eje_cpu):
        eje.grid(True, color="#e7e6e1", linewidth=1)
        eje.spines[["top", "right"]].set_visible(False)
        eje.legend(frameon=False, fontsize=9)
    figura.tight_layout()
    figura.savefig(destino, dpi=120)
    plt.close(figura)


def fila_carga(prefijo: str) -> dict[str, Any]:
    resumen = leer_agregado(RESULTADOS / f"{prefijo}_stats.csv")
    fila: dict[str, Any] = {"resumen": resumen}
    ruta_ws = RESULTADOS / f"{prefijo}_ws_eventos.csv"
    if ruta_ws.exists():
        fila["ws"] = resumir(leer_eventos(ruta_ws))
    ruta_cpu = RESULTADOS / f"{prefijo}_cpu.csv"
    if ruta_cpu.exists():
        muestras = leer_muestras(ruta_cpu)
        activas = [m for m in muestras if m["generador"] > 0] or muestras
        fila["cpu_generador_max"] = max((m["generador"] for m in activas), default=-1.0)
        fila["cpu_servidor_max"] = max((m["servidor"] for m in activas), default=-1.0)
    return fila


COLUMNAS_CARGA = [
    "Escenario",
    "Peticiones REST",
    "p95 REST (ms)",
    "Mediana (ms)",
    "Fallos (%)",
    "Peticiones/s",
    "CPU Locust máx. (%)",
    "CPU servidor máx. (%)",
    "WS conexiones (fallidas)",
    "WS mensajes (por s)",
    "WS difusión p50 / p95 (ms)",
]


def tabla_carga(filas: list[tuple[str, dict[str, Any]]]) -> str:
    lineas = [fila_md(COLUMNAS_CARGA), fila_md(["---"] * len(COLUMNAS_CARGA))]
    for etiqueta, f in filas:
        r = f["resumen"]
        ws = f.get("ws")
        celdas_ws = ["—", "—", "—"]
        if ws:
            celdas_ws = [
                f"{ws['conexiones_ok']} ({ws['conexiones_fallidas']})",
                f"{ws['mensajes']} ({ws['mensajes_por_s']:.0f})",
                f"{_texto(ws['latencia_p50_ms'])} / {_texto(ws['latencia_p95_ms'])}",
            ]
        celdas = [
            etiqueta,
            str(r.peticiones),
            f"{r.p95_ms:.0f}",
            f"{r.mediana_ms:.0f}",
            f"{r.fallos_pct:.2f}",
            f"{r.rps:.1f}",
            _texto(f.get("cpu_generador_max")),
            _texto(f.get("cpu_servidor_max")),
        ]
        lineas.append(fila_md(celdas + celdas_ws))
    return "\n".join(lineas)


def main() -> int:
    if len(sys.argv) < 4 or sys.argv[1] not in ("quiebre", "carga"):
        print(__doc__)
        return 2
    modo, salida = sys.argv[1], sys.argv[2]
    corridas = [tuple(arg.split("=", 1)) for arg in sys.argv[3:]]
    if modo == "carga":
        texto = tabla_carga([(etiqueta, fila_carga(prefijo)) for prefijo, etiqueta in corridas])
    else:
        series = [(etiqueta, cargar_quiebre(prefijo)) for prefijo, etiqueta in corridas]
        graficar_quiebre(series, RESULTADOS / f"{salida}.png")
        texto = "\n\n".join(tabla_quiebre(etiqueta, filas) for etiqueta, filas in series)
    (RESULTADOS / f"{salida}.md").write_text(texto + "\n", encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
