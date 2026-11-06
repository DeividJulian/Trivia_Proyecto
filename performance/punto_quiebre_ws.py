"""Punto de quiebre con REST + WebSocket: mismos escalones que punto_quiebre.py, mismos usuarios que
locustfile_ws.py (cada jugador con su WebSocket abierto).

Uso (CMD, con el servidor en otra terminal):
  set QUIEBRE_INICIO=50 && set QUIEBRE_INCREMENTO=50
  set QUIEBRE_SEGUNDOS_ESCALON=20 && set QUIEBRE_MAXIMO=1000
  locust -f performance\\punto_quiebre_ws.py --host http://127.0.0.1:8000 --headless ^
         --csv performance\\resultados\\quiebre_ws_local --csv-full-history
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from locustfile_ws import JugadorWebSocket, Presentador  # noqa: E402, F401 - Locust toma los usuarios de aquí
from punto_quiebre import EscalonesHastaQuiebre  # noqa: E402, F401 - misma forma de carga por escalones
