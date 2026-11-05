"""Genera un veredicto reproducible a partir de las evidencias del pipeline."""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
COBERTURA_MINIMA = 85.0
SEVERIDADES_BLOQUEANTES = {"HIGH", "CRITICAL"}


@dataclass(frozen=True)
class Compuerta:
    nombre: str
    estado: str
    evidencia: str

    @property
    def aprobada(self) -> bool:
        return self.estado == "APROBADA"


def comprobar_job(nombre: str, resultado: str) -> Compuerta:
    aprobado = resultado == "success"
    return Compuerta(nombre, "APROBADA" if aprobado else "FALLIDA", f"resultado del job: {resultado}")


def leer_junit(ruta: Path, nombre: str) -> Compuerta:
    try:
        raiz = ET.parse(ruta).getroot()  # noqa: S314 - XML generado por pytest dentro del pipeline
    except FileNotFoundError:
        return Compuerta(nombre, "FALLIDA", f"falta {ruta.name}")
    except ET.ParseError:
        return Compuerta(nombre, "FALLIDA", f"{ruta.name} no es XML válido")

    casos = raiz.findall(".//testcase")
    fallidas = sum(len(caso.findall("failure")) + len(caso.findall("error")) for caso in casos)
    omitidas = sum(len(caso.findall("skipped")) for caso in casos)
    if not casos:
        return Compuerta(nombre, "FALLIDA", "JUnit no contiene casos de prueba")
    estado = "APROBADA" if fallidas == 0 else "FALLIDA"
    return Compuerta(nombre, estado, f"{len(casos)} pruebas; {fallidas} fallidas; {omitidas} omitidas")


def leer_cobertura(ruta: Path) -> Compuerta:
    try:
        raiz = ET.parse(ruta).getroot()  # noqa: S314 - XML generado por pytest dentro del pipeline
        cobertura = float(raiz.attrib["line-rate"]) * 100
    except FileNotFoundError:
        return Compuerta("Cobertura", "FALLIDA", f"falta {ruta.name}")
    except (ET.ParseError, KeyError, ValueError):
        return Compuerta("Cobertura", "FALLIDA", f"{ruta.name} no contiene cobertura válida")

    estado = "APROBADA" if cobertura >= COBERTURA_MINIMA else "FALLIDA"
    return Compuerta("Cobertura", estado, f"{cobertura:.2f} %; mínimo {COBERTURA_MINIMA:.0f} %")


def leer_mutantes(ruta: Path) -> Compuerta:
    try:
        contenido = ruta.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Compuerta("Mutantes", "FALLIDA", f"falta {ruta.name}")

    coincidencia = re.search(r"Mutantes detectados:\s*(\d+)/(\d+)", contenido)
    if not coincidencia:
        return Compuerta("Mutantes", "FALLIDA", "no se encontró el resumen de mutantes")
    detectados, total = map(int, coincidencia.groups())
    estado = "APROBADA" if total == 6 and detectados == total else "FALLIDA"
    return Compuerta("Mutantes", estado, f"{detectados}/{total} detectados; se exige 6/6")


def leer_trivy(rutas: list[Path]) -> Compuerta:
    vulnerabilidades: list[tuple[str, str]] = []
    hallazgos_config: list[tuple[str, str]] = []
    errores: list[str] = []
    for ruta in rutas:
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except FileNotFoundError:
            errores.append(f"falta {ruta.name}")
            continue
        except json.JSONDecodeError:
            errores.append(f"{ruta.name} no es JSON válido")
            continue

        for resultado in datos.get("Results") or []:
            for campo, destino in (
                ("Vulnerabilities", vulnerabilidades),
                ("Secrets", vulnerabilidades),
                ("Misconfigurations", hallazgos_config),
            ):
                for hallazgo in resultado.get(campo) or []:
                    severidad = str(hallazgo.get("Severity", "UNKNOWN")).upper()
                    if severidad in SEVERIDADES_BLOQUEANTES:
                        identificador = hallazgo.get("VulnerabilityID") or hallazgo.get("ID") or campo
                        destino.append((severidad, str(identificador)))

    if errores:
        return Compuerta("Trivy", "FALLIDA", "; ".join(errores))
    bloqueantes = vulnerabilidades + hallazgos_config
    if bloqueantes:
        detalle = ", ".join(f"{severidad} {identificador}" for severidad, identificador in bloqueantes)
        return Compuerta("Trivy", "FALLIDA", detalle)
    return Compuerta("Trivy", "APROBADA", f"{len(rutas)} informes sin hallazgos HIGH/CRITICAL")


def leer_rendimiento(ruta: Path) -> Compuerta:
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from performance.verificar_umbrales import evaluar, leer_agregado

    try:
        resumen = leer_agregado(ruta)
    except (FileNotFoundError, ValueError, KeyError):
        return Compuerta("Rendimiento", "FALLIDA", f"no se pudo leer {ruta.name}")
    resultados = evaluar(resumen)
    evidencia = "; ".join(f"{nombre}: {medido} (umbral {umbral})" for nombre, medido, umbral, _ in resultados)
    estado = "APROBADA" if all(cumple for *_, cumple in resultados) else "FALLIDA"
    return Compuerta("Rendimiento", estado, evidencia)


def leer_sonar(ruta: Path, resultado_job: str) -> Compuerta:
    if resultado_job != "success":
        return Compuerta("SonarCloud", "PENDIENTE", "integración diferida; falta Quality Gate aprobado")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Compuerta("SonarCloud", "FALLIDA", f"falta {ruta.name}")
    except json.JSONDecodeError:
        return Compuerta("SonarCloud", "FALLIDA", f"{ruta.name} no es JSON válido")

    aprobado = datos.get("quality_gate") == "PASSED"
    estado = "APROBADA" if aprobado else "FALLIDA"
    return Compuerta("SonarCloud", estado, f"Quality Gate: {datos.get('quality_gate', 'desconocido')}")


def defectos_abiertos_altos(ruta: Path) -> Compuerta:
    contenido = ruta.read_text(encoding="utf-8")
    secciones = re.split(r"(?=^### DEF-)", contenido, flags=re.MULTILINE)
    abiertos = []
    for seccion in secciones:
        if re.search(r"\|\s*Severidad\s*\|\s*(?:Alta|Crítica)\s*\|", seccion, re.IGNORECASE) and re.search(
            r"\|\s*Estado\s*\|\s*(?:\*\*)?Abierto(?:\*\*)?\s*\|", seccion, re.IGNORECASE
        ):
            titulo = seccion.splitlines()[0].removeprefix("### ").strip()
            abiertos.append(titulo)
    estado = "FALLIDA" if abiertos else "APROBADA"
    evidencia = ", ".join(abiertos) if abiertos else "ningún defecto Alto/Crítico abierto"
    return Compuerta("Defectos", estado, evidencia)


def construir_reporte(compuertas: list[Compuerta]) -> str:
    apto = all(compuerta.aprobada for compuerta in compuertas)
    veredicto = "APTO PARA DESPLEGAR" if apto else "NO DESPLEGAR"
    filas = ["| Compuerta | Estado | Evidencia |", "|---|---|---|"]
    for compuerta in compuertas:
        evidencia = compuerta.evidencia.replace("|", "\\|")
        filas.append(f"| {compuerta.nombre} | {compuerta.estado} | {evidencia} |")
    return "# Reporte de predespliegue\n\n" + f"## Veredicto: **{veredicto}**\n\n" + "\n".join(filas) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=RAIZ / "reportes")
    parser.add_argument("--style-result", required=True)
    parser.add_argument("--tests-result", required=True)
    parser.add_argument("--mutants-result", required=True)
    parser.add_argument("--security-result", required=True)
    parser.add_argument("--performance-result", required=True)
    parser.add_argument("--sonar-result", default="pending")
    argumentos = parser.parse_args()

    directorio = argumentos.report_dir
    compuertas = [
        comprobar_job("Estilo", argumentos.style_result),
        comprobar_job("Pruebas", argumentos.tests_result),
        leer_junit(directorio / "junit" / "componente.xml", "Componente"),
        leer_junit(directorio / "junit" / "integracion.xml", "Integración"),
        leer_junit(directorio / "junit" / "sistema.xml", "Sistema"),
        leer_junit(directorio / "junit" / "aceptacion.xml", "Aceptación"),
        leer_junit(directorio / "junit" / "suite.xml", "Suite completa"),
        leer_cobertura(directorio / "coverage.xml"),
        comprobar_job("Efectividad de pruebas", argumentos.mutants_result),
        leer_mutantes(directorio / "mutantes.txt"),
        comprobar_job("Seguridad", argumentos.security_result),
        leer_trivy(
            [
                directorio / "trivy-fs.json",
                directorio / "trivy-config.json",
                directorio / "trivy-image.json",
            ]
        ),
        comprobar_job("Ejecución de rendimiento", argumentos.performance_result),
        leer_rendimiento(directorio / "performance" / "run_stats.csv"),
        leer_sonar(directorio / "quality-gate.json", argumentos.sonar_result),
        defectos_abiertos_altos(RAIZ / "docs" / "REPORTE_DEFECTOS.md"),
    ]
    directorio.mkdir(parents=True, exist_ok=True)
    salida = directorio / "REPORTE_PREDESPLIEGUE.md"
    reporte = construir_reporte(compuertas)
    salida.write_text(reporte, encoding="utf-8")
    print(reporte)
    return 0 if all(compuerta.aprobada for compuerta in compuertas) else 1


if __name__ == "__main__":
    raise SystemExit(main())
