"""Modo Saboteador: mutantes controlados.

Cada sabotaje es un "mutante": una rama alternativa del código que solo se ejecuta si
esta_activo("clave") es verdadero. El código nunca se modifica en caliente.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Sabotaje:
    """Descripción de un mutante y del nivel de prueba que debería detectarlo."""

    clave: str
    nombre: str
    modulo: str
    descripcion: str
    nivel_que_lo_detecta: str
    # Explicación para quien usa el panel: qué regla rompe, cómo debería ser y cómo notarlo jugando.
    que_sabotea: str = ""
    comportamiento_correcto: str = ""
    comportamiento_saboteado: str = ""
    como_notarlo: str = ""


CATALOGO: dict[str, Sabotaje] = {}


def _registrar(sabotaje: Sabotaje) -> None:
    CATALOGO[sabotaje.clave] = sabotaje


# --- Catálogo de mutantes ----------------------------------------------------------------------


_registrar(
    Sabotaje(
        clave="tiempo_estricto",
        nombre="Tiempo estricto",
        modulo="puntaje",
        descripcion="es_respuesta_a_tiempo usa < en vez de <=: responder justo en el límite deja de contar.",
        nivel_que_lo_detecta="componente (valores límite) y sistema (extremo a extremo)",
        que_sabotea="La regla que decide si una respuesta llegó a tiempo (función es_respuesta_a_tiempo).",
        comportamiento_correcto=(
            "Una respuesta que llega EXACTAMENTE en el último instante (20,0 s de 20 s) cuenta como a tiempo "
            "y, si es correcta, vale 1000 puntos."
        ),
        comportamiento_saboteado=(
            "Se compara con < en lugar de <=: la respuesta justo en el límite se toma como tarde, vale 0 "
            "puntos y reinicia la racha. Las respuestas que llegan antes del límite NO cambian."
        ),
        como_notarlo=(
            "Jugando a mano casi no se ve: hay que responder en el milisegundo exacto del límite. Por eso "
            "existe la prueba de valores límite. Ejemplo: responder bien a los 20,000 s de 20 s da 0 puntos "
            "en vez de 1000."
        ),
    )
)

_registrar(
    Sabotaje(
        clave="racha_no_suma",
        nombre="Racha que no suma",
        modulo="puntaje",
        descripcion="sumar_racha no aumenta la racha al acertar: nunca hay bono de racha.",
        nivel_que_lo_detecta="componente (racha) e integración (puntaje + racha + ranking)",
        que_sabotea="El contador de aciertos seguidos (racha) y su bono.",
        comportamiento_correcto=(
            "Cada acierto seguido suma 1 a la racha. Desde el 2.º acierto seguido se gana un bono de +100 "
            "por acierto (2.º: +100, 3.º: +200…) con un tope de +500. Fallar la deja en 0."
        ),
        comportamiento_saboteado=(
            "Al acertar, la racha no aumenta: se queda en 0 y nunca hay bono de racha. Los 1000 puntos base "
            "y el bono por velocidad siguen funcionando bien."
        ),
        como_notarlo=(
            "En la pestaña Jugador, «Racha» sigue en 0 aunque aciertes varias seguidas, y la 2.ª, 3.ª… "
            "respuesta correcta da 100, 200… puntos menos de lo que debería."
        ),
    )
)

_registrar(
    Sabotaje(
        clave="bono_sin_acierto",
        nombre="Bono sin acierto",
        modulo="puntaje",
        descripcion="Reproduce el error de la v2: una respuesta incorrecta recibe el bono por velocidad.",
        nivel_que_lo_detecta="componente, sistema (extremo a extremo) y aceptación (HU-02)",
        que_sabotea="El cálculo de puntos de una respuesta INCORRECTA (función calcular_puntos).",
        comportamiento_correcto="Una respuesta incorrecta vale 0 puntos, sin importar lo rápida que sea.",
        comportamiento_saboteado=(
            "La respuesta incorrecta recibe el bono por velocidad: hasta 500 puntos si se responde al "
            "instante (no recibe los 1000 base). Es el mismo error de la versión v2 (DEF-011)."
        ),
        como_notarlo=(
            "Responde MAL y muy rápido: en vez de «0 puntos» aparece algo como «+475 puntos». Quien adivina "
            "rápido puede quedar por encima de quien sabe pero piensa la respuesta."
        ),
    )
)

_registrar(
    Sabotaje(
        clave="empates_mal",
        nombre="Empates mal resueltos",
        modulo="ranking",
        descripcion="El ranking no desempata por tiempo total: con igualdad de puntos ordena por nombre.",
        nivel_que_lo_detecta="componente (ranking) e integración (partida)",
        que_sabotea="El orden del ranking cuando dos jugadores tienen los mismos puntos (desempate).",
        comportamiento_correcto=(
            "A igualdad de puntos va primero quien tardó MENOS en total en responder; si también empatan "
            "en tiempo, se ordenan alfabéticamente."
        ),
        comportamiento_saboteado=(
            "Se ignora el tiempo: los empates se ordenan solo por nombre (A → Z). Los puntos y los tiempos "
            "de cada jugador no cambian; solo cambia quién aparece primero."
        ),
        como_notarlo=(
            "Haz que dos jugadores sumen lo mismo (por ejemplo, ambos fallan todo: 0 puntos) y que «Beto» "
            "responda más rápido que «Ana». Correcto: Beto primero. Saboteado: Ana primero, por el nombre."
        ),
    )
)

_registrar(
    Sabotaje(
        clave="no_guarda_respuesta",
        nombre="No guarda la respuesta",
        modulo="partida",
        descripcion="La partida suma puntos pero no registra la respuesta: se puede responder varias veces.",
        nivel_que_lo_detecta="integración (partida) y sistema (409 al responder dos veces)",
        que_sabotea="El registro de quién ya respondió la pregunta actual (Partida.responder).",
        comportamiento_correcto=(
            "La partida anota cada respuesta: cada jugador responde UNA sola vez por pregunta (un 2.º "
            "intento da error 409) y, cuando todos respondieron, la pregunta se cierra sola."
        ),
        comportamiento_saboteado=(
            "Los puntos se suman pero la respuesta no queda anotada: el mismo jugador puede responder "
            "varias veces y sumar puntos cada vez; el contador «respondieron» se queda en 0 y la pregunta "
            "ya no se cierra sola."
        ),
        como_notarlo=(
            "En la pestaña Profesor se ve «respondieron 0 de N» aunque todos hayan respondido, y hay que "
            "cerrar la pregunta a mano. (El front desactiva los botones tras responder; desde /docs se puede "
            "enviar la misma respuesta dos veces y ambas suman.)"
        ),
    )
)

_registrar(
    Sabotaje(
        clave="respuesta_lenta",
        nombre="Respuesta lenta",
        modulo="api",
        descripcion="POST /respuestas tarda 1,5 s antes de responder (incumple RNF-03).",
        nivel_que_lo_detecta="sistema, no funcional (tiempo de respuesta < 0,5 s)",
        que_sabotea="La velocidad del servidor al recibir una respuesta (requisito no funcional RNF-03).",
        comportamiento_correcto="POST /respuestas contesta en milisegundos (RNF-03 exige menos de 0,5 s).",
        comportamiento_saboteado=(
            "El servidor espera 1,5 s antes de procesar cada respuesta. Las reglas del juego no cambian, "
            "pero como el tiempo se mide cuando el servidor procesa, cada respuesta pierde unos 37 puntos "
            "de bono por velocidad (1,5 s de 20 s)."
        ),
        como_notarlo=(
            "Al pulsar una opción, el mensaje con los puntos tarda 1,5 s en aparecer. Es un fallo NO "
            "funcional: el resultado es casi correcto, pero lento."
        ),
    )
)


# --- Estado: qué sabotajes están activos -------------------------------------------------------

RETARDO_RESPUESTA_LENTA_S = 1.5

_activos: set[str] = set()


def _validar(clave: str) -> str:
    if clave not in CATALOGO:
        disponibles = ", ".join(sorted(CATALOGO)) or "ninguno"
        raise KeyError(f"Sabotaje desconocido: '{clave}'. Disponibles: {disponibles}.")
    return clave


def esta_activo(clave: str) -> bool:
    """True si el mutante indicado está activo."""
    return clave in _activos


def activar(clave: str) -> None:
    _activos.add(_validar(clave))


def desactivar(clave: str) -> None:
    _activos.discard(_validar(clave))


def desactivar_todos() -> None:
    _activos.clear()


def activos() -> list[str]:
    """Claves de los sabotajes activos, ordenadas."""
    return sorted(_activos)


def leer_activos_del_entorno(valor: str | None = None) -> list[str]:
    """Activa los sabotajes listados en la variable SABOTAJES (separados por comas).

    Lo usa verificar_mutantes.py para ejecutar la suite con un mutante activo.
    """
    texto = os.environ.get("SABOTAJES", "") if valor is None else valor
    claves = [clave.strip() for clave in texto.split(",") if clave.strip()]
    for clave in claves:
        activar(clave)
    return claves


leer_activos_del_entorno()
