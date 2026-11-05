"""Mapa de impacto: qué módulos dependen de cuál (docs/ANALISIS_IMPACTO.md)."""

from collections import deque
from collections.abc import Iterable

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
