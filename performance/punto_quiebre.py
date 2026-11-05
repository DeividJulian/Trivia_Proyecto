"""Prueba de estrés por escalones hasta encontrar el punto de quiebre.

Sube los usuarios de a escalones y se detiene cuando un escalón supera los límites de quiebre:
más del 5 % de fallos o p95 mayor a 2000 ms (PLAN_DE_PRUEBAS.md). Usa los mismos usuarios que
locustfile.py (presentadores y jugadores).

Variables de entorno (valores por defecto entre paréntesis):
  QUIEBRE_INICIO (25)  QUIEBRE_INCREMENTO (25)  QUIEBRE_SEGUNDOS_ESCALON (20)  QUIEBRE_MAXIMO (500)

Uso (CMD, con el servidor en otra terminal):
  locust -f performance\\punto_quiebre.py --host http://localhost:8000 --headless ^
         --csv performance\\resultados\\quiebre_local --csv-full-history
  python performance\\analizar_resultados.py quiebre_local
"""

import logging
import os
import sys
from pathlib import Path

from locust import LoadTestShape

sys.path.insert(0, str(Path(__file__).resolve().parent))

from locustfile import Jugador, Presentador  # noqa: E402, F401 - Locust toma los usuarios de este módulo
from verificar_umbrales import supera_quiebre  # noqa: E402 - mismo directorio, agregado arriba a sys.path

logger = logging.getLogger("punto_quiebre")


def _entero(nombre: str, por_defecto: int) -> int:
    valor = os.environ.get(nombre, "").strip()
    return int(valor) if valor else por_defecto


class EscalonesHastaQuiebre(LoadTestShape):
    """Escalones de usuarios; al final de cada uno evalúa fallos y p95 del escalón."""

    def __init__(self) -> None:
        super().__init__()
        self.inicio = _entero("QUIEBRE_INICIO", 25)
        self.incremento = _entero("QUIEBRE_INCREMENTO", 25)
        self.segundos = _entero("QUIEBRE_SEGUNDOS_ESCALON", 20)
        self.maximo = _entero("QUIEBRE_MAXIMO", 500)
        self._escalon = 0
        self._peticiones_inicio = 0
        self._fallos_inicio = 0

    def usuarios_del_escalon(self, escalon: int) -> int:
        return self.inicio + escalon * self.incremento

    def tick(self) -> tuple[int, float] | None:
        escalon = int(self.get_run_time() // self.segundos)
        if escalon != self._escalon:
            if self._cerrar_escalon():
                return None
            self._escalon = escalon
        usuarios = self.usuarios_del_escalon(escalon)
        if usuarios > self.maximo:
            logger.warning("Se alcanzó QUIEBRE_MAXIMO=%s sin llegar al punto de quiebre.", self.maximo)
            return None
        return usuarios, float(max(self.incremento, 1))

    def _cerrar_escalon(self) -> bool:
        """Evalúa el escalón que termina. Devuelve True si se cruzó el punto de quiebre."""
        total = self.runner.stats.total
        peticiones = total.num_requests - self._peticiones_inicio
        fallos = total.num_failures - self._fallos_inicio
        self._peticiones_inicio, self._fallos_inicio = total.num_requests, total.num_failures
        fallos_pct = 100.0 * fallos / peticiones if peticiones else 0.0
        p95 = total.get_current_response_time_percentile(0.95) or 0.0
        usuarios = self.usuarios_del_escalon(self._escalon)
        logger.warning(
            "Escalón %s: %s usuarios, %s peticiones, fallos %.2f %%, p95 %.0f ms",
            self._escalon + 1,
            usuarios,
            peticiones,
            fallos_pct,
            p95,
        )
        if supera_quiebre(fallos_pct, p95):
            logger.warning("PUNTO DE QUIEBRE en %s usuarios: se detiene la prueba.", usuarios)
            return True
        return False
