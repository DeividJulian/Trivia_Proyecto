"""Partida: máquina de estados de una trivia en vivo."""

import time
from collections.abc import Callable, Sequence
from dataclasses import asdict
from typing import Any

from app.dominio import sabotajes
from app.dominio.errores import ErrorPartida
from app.dominio.modelos import (
    NUMERO_OPCIONES,
    EstadoPartida,
    ImpactoRespuesta,
    Jugador,
    Pregunta,
    Respuesta,
)
from app.dominio.puntaje import calcular_puntos
from app.dominio.ranking import FilaRanking, obtener_ganador, ordenar_ranking

Reloj = Callable[[], float]

LONGITUD_MAX_NOMBRE = 20
MAX_JUGADORES_POR_DEFECTO = 50


class Partida:
    """Una partida identificada por su PIN.

    El reloj se inyecta (por defecto time.monotonic) para que las pruebas controlen el tiempo
    sin esperar de verdad.
    """

    def __init__(
        self,
        pin: str,
        preguntas: Sequence[Pregunta],
        reloj: Reloj = time.monotonic,
        max_jugadores: int = MAX_JUGADORES_POR_DEFECTO,
    ) -> None:
        if not preguntas:
            raise ValueError("Una partida necesita al menos una pregunta.")
        self.pin = pin
        self.preguntas = list(preguntas)
        self.max_jugadores = max_jugadores
        self._reloj = reloj
        self.estado = EstadoPartida.LOBBY
        self.jugadores: dict[str, Jugador] = {}
        self.indice_pregunta = -1
        self.respuestas: dict[str, Respuesta] = {}
        self.puntos_ronda: dict[str, int] = {}
        self._respuestas_reales: dict[str, Respuesta] = {}
        self.impacto: list[ImpactoRespuesta] = []
        self._impacto_desglose: list[dict[str, int]] = []
        self._inicio_pregunta: float | None = None
        self.ultima_actividad = reloj()

    def _tocar(self) -> None:
        """Registra actividad (la usa el gestor para limpiar partidas inactivas)."""
        self.ultima_actividad = self._reloj()

    @property
    def pregunta_actual(self) -> Pregunta | None:
        """Pregunta en curso, o None si la partida no ha empezado."""
        if 0 <= self.indice_pregunta < len(self.preguntas):
            return self.preguntas[self.indice_pregunta]
        return None

    def buscar_jugador(self, nombre: str) -> Jugador | None:
        """Busca un jugador sin distinguir mayúsculas de minúsculas ni espacios en los extremos."""
        clave = (nombre or "").strip().casefold()
        for jugador in self.jugadores.values():
            if jugador.nombre.casefold() == clave:
                return jugador
        return None

    def unirse(self, nombre: str) -> Jugador:
        """Agrega un jugador: solo en LOBBY, nombre de 1 a 20 caracteres, sin repetir y con cupo."""
        if self.estado != EstadoPartida.LOBBY:
            raise ErrorPartida("La partida ya comenzó: no se admiten más jugadores.")
        nombre = (nombre or "").strip()
        if not 1 <= len(nombre) <= LONGITUD_MAX_NOMBRE:
            raise ErrorPartida(f"El nombre debe tener entre 1 y {LONGITUD_MAX_NOMBRE} caracteres.")
        if self.buscar_jugador(nombre) is not None:
            raise ErrorPartida(f"Ya hay un jugador llamado '{nombre}' en la partida.")
        if len(self.jugadores) >= self.max_jugadores:
            raise ErrorPartida(f"La partida está llena: máximo {self.max_jugadores} jugadores.")
        jugador = Jugador(nombre=nombre)
        self.jugadores[nombre] = jugador
        self._tocar()
        return jugador

    # --- Flujo del juego ---------------------------------------------------------------------------

    def _mostrar_pregunta(self, indice: int) -> None:
        """Pasa a la pregunta indicada y arranca su cronómetro."""
        self.indice_pregunta = indice
        self.estado = EstadoPartida.PREGUNTA
        self._inicio_pregunta = self._reloj()
        self.respuestas = {}
        self.puntos_ronda = {}
        self._respuestas_reales = {}

    def iniciar(self) -> None:
        """LOBBY → PREGUNTA. Exige al menos un jugador."""
        if self.estado != EstadoPartida.LOBBY:
            raise ErrorPartida("La partida ya fue iniciada.")
        if not self.jugadores:
            raise ErrorPartida("Se necesita al menos un jugador para iniciar.")
        self._mostrar_pregunta(0)
        self._tocar()

    def tiempo_transcurrido(self) -> float:
        """Segundos desde que se mostró la pregunta actual."""
        if self._inicio_pregunta is None:
            return 0.0
        return max(0.0, self._reloj() - self._inicio_pregunta)

    def tiempo_restante(self) -> float:
        """Segundos que quedan para responder (0 fuera del estado PREGUNTA)."""
        pregunta = self.pregunta_actual
        if self.estado != EstadoPartida.PREGUNTA or pregunta is None:
            return 0.0
        return max(0.0, pregunta.tiempo_limite - self.tiempo_transcurrido())

    def responder(self, nombre: str, opcion: int, tiempo_recibido: float | None = None) -> int:
        """Registra la respuesta de un jugador y devuelve los puntos que ganó.

        Solo en PREGUNTA y una vez por jugador. Una respuesta fuera de tiempo se acepta pero vale 0
        y reinicia la racha. Si ya respondieron todos, la pregunta se cierra sola.
        tiempo_recibido: marca de tiempo al llegar la petición a la API (antes del mutante respuesta_lenta).
        """
        if self.estado != EstadoPartida.PREGUNTA:
            raise ErrorPartida("Solo se puede responder mientras hay una pregunta abierta.")
        jugador = self.buscar_jugador(nombre)
        if jugador is None:
            raise ErrorPartida(f"'{nombre}' no está en la partida.")
        if not 0 <= opcion < NUMERO_OPCIONES:
            raise ErrorPartida(f"La opción debe estar entre 0 y {NUMERO_OPCIONES - 1}.")
        if jugador.nombre in self.respuestas:
            raise ErrorPartida(f"{jugador.nombre} ya respondió esta pregunta.")

        pregunta = self.pregunta_actual
        if pregunta is None:
            raise ErrorPartida("No hay una pregunta abierta.")

        tiempo = self.tiempo_transcurrido()
        tiempo_real = tiempo if tiempo_recibido is None else max(0.0, tiempo_recibido)
        segundos_extra = round(max(0.0, tiempo - tiempo_real), 3)

        es_correcta = opcion == pregunta.correcta

        # Puntos y racha mostrados (con mutantes activos)
        puntos, jugador.racha = calcular_puntos(es_correcta, tiempo, pregunta.tiempo_limite, jugador.racha)
        jugador.puntos += puntos
        jugador.tiempo_total += tiempo
        if not sabotajes.esta_activo("no_guarda_respuesta"):  # MUTANTE: si está activo no se registra
            self.respuestas[jugador.nombre] = Respuesta(opcion=opcion, tiempo_respuesta=tiempo)
        self.puntos_ronda[jugador.nombre] = puntos
        self._tocar()

        # Evaluación sombra (reales como si no hubiera ningún sabotaje)
        ya_habia_respondido = jugador.nombre in self._respuestas_reales
        activos_actuales = tuple(sabotajes.activos())
        desglose_resp: dict[str, int] = {}

        if ya_habia_respondido:
            # Sin el mutante no_guarda_respuesta, la 2.ª respuesta habría sido rechazada con 409
            puntos_reales = 0
            racha_real_nueva = jugador.racha_real
            nota = "respuesta repetida: sin el sabotaje habría sido rechazada (409)"
            desglose_resp["no_guarda_respuesta"] = puntos
        else:
            with sabotajes.sin_sabotajes():
                puntos_reales, racha_real_nueva = calcular_puntos(
                    es_correcta, tiempo_real, pregunta.tiempo_limite, jugador.racha_real
                )
            jugador.puntos_reales += puntos_reales
            racha_real_anterior = jugador.racha_real  # DEF-033: el desglose usa la racha previa
            jugador.racha_real = racha_real_nueva
            jugador.tiempo_total_real += tiempo_real
            self._respuestas_reales[jugador.nombre] = Respuesta(opcion=opcion, tiempo_respuesta=tiempo_real)

            diff_total = puntos - puntos_reales
            if len(activos_actuales) == 1 and diff_total != 0:
                desglose_resp[activos_actuales[0]] = diff_total
            elif len(activos_actuales) > 1 and diff_total != 0:
                for clave in activos_actuales:
                    with sabotajes.solo_sabotajes([clave]):
                        t_clave = tiempo if clave == "respuesta_lenta" else tiempo_real
                        pts_clave, _ = calcular_puntos(
                            es_correcta, t_clave, pregunta.tiempo_limite, racha_real_anterior
                        )
                    diff_clave = pts_clave - puntos_reales
                    if diff_clave != 0:
                        desglose_resp[clave] = diff_clave

            if "bono_sin_acierto" in activos_actuales and not es_correcta and puntos > 0:
                nota = f"recibió +{puntos} que no le correspondían (bono_sin_acierto)"
            elif "racha_no_suma" in activos_actuales and puntos < puntos_reales:
                nota = f"perdió {abs(diff_total)} pts por racha no sumada (racha_no_suma)"
            elif "tiempo_estricto" in activos_actuales and puntos == 0 and puntos_reales > 0:
                nota = "respuesta en el límite tomada como tardía (tiempo_estricto)"
            elif "respuesta_lenta" in activos_actuales and segundos_extra > 0:
                nota = f"+{segundos_extra:.1f} s y {diff_total} pts de bono por respuesta_lenta"
            elif diff_total != 0:
                nota = f"diferencia de {diff_total:+d} pts por sabotaje"
            else:
                nota = "correcta" if es_correcta else "incorrecta"

        diferencia = puntos - puntos_reales
        registro_impacto = ImpactoRespuesta(
            numero_pregunta=self.indice_pregunta + 1,
            jugador=jugador.nombre,
            opcion=opcion,
            correcta=es_correcta,
            sabotajes_activos=activos_actuales,
            puntos_mostrados=puntos,
            puntos_reales=puntos_reales,
            diferencia=diferencia,
            racha_mostrada=jugador.racha,
            racha_real=racha_real_nueva,
            segundos_extra=segundos_extra,
            nota=nota,
        )
        self.impacto.append(registro_impacto)
        self._impacto_desglose.append(desglose_resp)

        if len(self.respuestas) == len(self.jugadores):
            self.cerrar_pregunta()
        return puntos

    def cerrar_pregunta(self) -> None:
        """PREGUNTA → RESULTADOS. Quien no respondió pierde la racha."""
        if self.estado != EstadoPartida.PREGUNTA:
            raise ErrorPartida("No hay una pregunta abierta para cerrar.")
        for jugador in self.jugadores.values():
            if jugador.nombre not in self.respuestas:
                jugador.racha = 0
            if jugador.nombre not in self._respuestas_reales:
                jugador.racha_real = 0
        self.estado = EstadoPartida.RESULTADOS
        self._tocar()

    def siguiente(self) -> None:
        """Avanza la partida: PREGUNTA → RESULTADOS, y RESULTADOS → PREGUNTA o FINALIZADA."""
        if self.estado == EstadoPartida.PREGUNTA:
            self.cerrar_pregunta()
        elif self.estado == EstadoPartida.RESULTADOS:
            if self.indice_pregunta + 1 < len(self.preguntas):
                self._mostrar_pregunta(self.indice_pregunta + 1)
            else:
                self.estado = EstadoPartida.FINALIZADA
            self._tocar()
        else:
            raise ErrorPartida(f"No se puede avanzar desde el estado {self.estado}.")

    # --- Resultados --------------------------------------------------------------------------------

    def ranking(self) -> list[FilaRanking]:
        """Ranking actual de la partida."""
        return ordenar_ranking(self.jugadores.values())

    def ranking_real(self) -> list[FilaRanking]:
        """Ranking calculado con puntos reales, tiempo total real y sin sabotajes."""
        jugadores_reales = [
            Jugador(
                nombre=j.nombre,
                puntos=j.puntos_reales,
                racha=j.racha_real,
                tiempo_total=j.tiempo_total_real,
            )
            for j in self.jugadores.values()
        ]
        with sabotajes.sin_sabotajes():
            return ordenar_ranking(jugadores_reales)

    def impacto_por_jugador(self) -> list[dict[str, Any]]:
        """Devuelve el impacto del sabotaje por cada jugador."""
        rank_mostrado = {fila.nombre: fila.posicion for fila in self.ranking()}
        rank_real = {fila.nombre: fila.posicion for fila in self.ranking_real()}

        resultado: list[dict[str, Any]] = []
        for jugador in sorted(
            self.jugadores.values(),
            key=lambda j: (rank_mostrado.get(j.nombre, 999), j.nombre.casefold()),
        ):
            desglose = {c: 0 for c in sabotajes.CATALOGO}
            for resp, atrib in zip(self.impacto, self._impacto_desglose, strict=False):
                if resp.jugador == jugador.nombre:
                    for c, delta in atrib.items():
                        desglose[c] = desglose.get(c, 0) + delta

            resultado.append(
                {
                    "jugador": jugador.nombre,
                    "puntos_mostrados": jugador.puntos,
                    "puntos_reales": jugador.puntos_reales,
                    "diferencia": jugador.puntos - jugador.puntos_reales,
                    "posicion_mostrada": rank_mostrado.get(jugador.nombre, 0),
                    "posicion_real": rank_real.get(jugador.nombre, 0),
                    "racha_mostrada": jugador.racha,
                    "racha_real": jugador.racha_real,
                    "desglose": desglose,
                }
            )
        return resultado

    def resumen_por_sabotaje(self) -> dict[str, dict[str, int]]:
        """Resumen por sabotaje: respuestas afectadas y puntos acumulados de diferencia."""
        resumen = {c: {"respuestas_afectadas": 0, "puntos_de_diferencia": 0} for c in sabotajes.CATALOGO}
        for _resp, atrib in zip(self.impacto, self._impacto_desglose, strict=False):
            for c, delta in atrib.items():
                if delta != 0:
                    resumen[c]["respuestas_afectadas"] += 1
                    resumen[c]["puntos_de_diferencia"] += delta
        return resumen

    def ganador(self) -> FilaRanking | None:
        """Ganador de la partida (None si no hay jugadores)."""
        return obtener_ganador(self.jugadores.values())

    def estado_publico(self) -> dict[str, Any]:
        """Estado que se puede enviar a todos los jugadores.

        La respuesta correcta solo se revela en RESULTADOS; mientras la pregunta está abierta
        nadie puede verla.
        """
        pregunta = self.pregunta_actual
        estado: dict[str, Any] = {
            "pin": self.pin,
            "estado": self.estado.value,
            "jugadores": [jugador.nombre for jugador in self.jugadores.values()],
            "numero_pregunta": self.indice_pregunta + 1,
            "total_preguntas": len(self.preguntas),
            "pregunta": None,
            "tiempo_restante": round(self.tiempo_restante(), 3),
            "respondieron": len(self.respuestas),
        }
        if pregunta is not None and self.estado in (EstadoPartida.PREGUNTA, EstadoPartida.RESULTADOS):
            estado["pregunta"] = {
                "texto": pregunta.texto,
                "opciones": list(pregunta.opciones),
                "tiempo_limite": pregunta.tiempo_limite,
            }
        if self.estado == EstadoPartida.RESULTADOS and pregunta is not None:
            estado["correcta"] = pregunta.correcta
            estado["puntos_ronda"] = dict(self.puntos_ronda)
        if self.estado in (EstadoPartida.RESULTADOS, EstadoPartida.FINALIZADA):
            estado["ranking"] = [asdict(fila) for fila in self.ranking()]
        if self.estado == EstadoPartida.FINALIZADA:
            ganador = self.ganador()
            estado["ganador"] = asdict(ganador) if ganador else None
        return estado
