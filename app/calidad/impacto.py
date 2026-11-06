"""Mapa de impacto: qué módulos dependen de cuál (docs/ANALISIS_IMPACTO.md)."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass

# módulo -> módulos que dependen directamente de él
DEPENDIENTES: dict[str, frozenset[str]] = {
    "Tiempo": frozenset({"Puntaje", "Racha"}),
    "Racha": frozenset({"Puntaje"}),
    "Puntaje": frozenset({"Ranking", "Partida"}),
    "Preguntas": frozenset({"Partida", "Gestor"}),
    "Partida": frozenset({"Ranking", "Gestor", "API"}),
    "Ranking": frozenset({"API"}),
    "Gestor": frozenset({"API"}),
    "API": frozenset(),
}

MODULOS = frozenset(DEPENDIENTES)


def dependientes_directos(modulo: str) -> frozenset[str]:
    """Módulos que usan directamente al indicado."""
    if modulo not in DEPENDIENTES:
        raise ValueError(f"Módulo desconocido: '{modulo}'. Conocidos: {', '.join(sorted(MODULOS))}.")
    return DEPENDIENTES[modulo]


def modulos_afectados(modulo: str) -> frozenset[str]:
    """Todos los módulos que pueden fallar si cambia el indicado (dependencia transitiva, sin él mismo)."""
    afectados: set[str] = set()
    pendientes = deque(dependientes_directos(modulo))
    while pendientes:
        actual = pendientes.popleft()
        if actual not in afectados:
            afectados.add(actual)
            pendientes.extend(DEPENDIENTES[actual])
    afectados.discard(modulo)
    return frozenset(afectados)


def impacto_de(modulos: Iterable[str]) -> frozenset[str]:
    """Módulos cambiados más todos sus afectados."""
    total: set[str] = set()
    for modulo in modulos:
        total.add(modulo)
        total |= modulos_afectados(modulo)
    return frozenset(total)


# --- De archivos cambiados a pruebas -----------------------------------------------------------

MARCADOR_DE_MODULO = {
    "Tiempo": "puntaje",
    "Racha": "puntaje",
    "Puntaje": "puntaje",
    "Preguntas": "preguntas",
    "Partida": "partida",
    "Ranking": "ranking",
    "Gestor": "gestor",
    "API": "api",
}

# prefijo de ruta -> módulos que contiene (el primero que coincide gana)
MODULOS_DE_ARCHIVO: tuple[tuple[str, frozenset[str]], ...] = (
    ("app/dominio/puntaje.py", frozenset({"Tiempo", "Racha", "Puntaje"})),
    ("app/dominio/ranking.py", frozenset({"Ranking"})),
    ("app/dominio/partida.py", frozenset({"Partida"})),
    ("app/dominio/gestor.py", frozenset({"Gestor"})),
    ("app/dominio/preguntas.py", frozenset({"Preguntas"})),
    ("data/", frozenset({"Preguntas"})),
    ("app/dominio/modelos.py", frozenset({"Preguntas", "Partida", "Ranking"})),
    ("app/dominio/errores.py", frozenset({"Partida", "Gestor", "API"})),
    ("app/api/", frozenset({"API"})),
    ("app/tiempo_real/", frozenset({"API"})),
    ("app/main.py", frozenset({"API"})),
    ("app/config.py", frozenset({"API"})),
)

# Archivos que no cambian el comportamiento: no exigen pruebas.
SIN_EFECTO = ("docs/", "README.md", "CLAUDE.md", ".gitignore", ".env.example")


@dataclass(frozen=True)
class PlanRegresion:
    """Qué pruebas ejecutar para un conjunto de archivos cambiados."""

    modulos_cambiados: frozenset[str]
    afectados: frozenset[str]
    pruebas_cambiadas: tuple[str, ...]
    suite_completa: bool
    motivo: str

    def argumentos_pytest(self) -> list[str]:
        """Argumentos para pytest: [] = nada que probar; ["-q"] = todo; o filtro por marcadores."""
        if self.suite_completa:
            return ["-q"]
        if self.afectados:
            marcadores = sorted({MARCADOR_DE_MODULO[m] for m in self.afectados})
            return ["-q", "-m", " or ".join(marcadores)]
        if self.pruebas_cambiadas:
            return ["-q", *self.pruebas_cambiadas]
        return []


def planificar_regresion(archivos: Iterable[str]) -> PlanRegresion:
    """Deduce los módulos cambiados a partir de las rutas y arma el plan de regresión."""
    modulos: set[str] = set()
    pruebas: list[str] = []
    desconocidos: list[str] = []
    for archivo in (a.replace("\\", "/") for a in archivos):
        if archivo.startswith(SIN_EFECTO):
            continue
        if archivo.startswith("tests/"):
            pruebas.append(archivo)
            continue
        coincidencia = next((m for prefijo, m in MODULOS_DE_ARCHIVO if archivo.startswith(prefijo)), None)
        if coincidencia is None:
            desconocidos.append(archivo)
        else:
            modulos |= coincidencia

    if desconocidos:
        motivo = f"Archivos sin módulo asignado ({', '.join(sorted(desconocidos))}): se ejecuta todo."
        return PlanRegresion(frozenset(modulos), impacto_de(modulos), tuple(pruebas), True, motivo)
    afectados = impacto_de(modulos)
    if afectados:
        motivo = f"Cambiaron {', '.join(sorted(modulos))}; afectados: {', '.join(sorted(afectados))}."
    elif pruebas:
        motivo = "Solo cambiaron pruebas: se ejecutan esas pruebas."
    else:
        motivo = "Solo cambió documentación: no hay pruebas que ejecutar."
    return PlanRegresion(frozenset(modulos), afectados, tuple(pruebas), False, motivo)
