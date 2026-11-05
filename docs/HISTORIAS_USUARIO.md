# Historias de usuario y criterios de aceptación

Cada historia tiene su prueba de aceptación en `tests/aceptacion/test_historias.py`. Esas pruebas
usan **solo la API pública** (HTTP y WebSocket), como lo haría un cliente real, y el reloj real del
servidor. Para saber qué opción es la correcta, el "estudiante que sabe" consulta el banco público
`data/preguntas.json`, igual que alguien que estudió el tema.

## HU-01 – Partida completa sin ayuda
**Como** profesor **quiero** crear una partida y que 3 estudiantes jueguen hasta el final sin ayuda
**para** usar TestQuiz en clase.

| # | Dado | Cuando | Entonces |
|---|---|---|---|
| 1 | Una partida recién creada y su PIN | 3 estudiantes se unen con ese PIN | La partida está en LOBBY con los 3 nombres |
| 2 | La partida con 3 jugadores | El profesor la inicia y avanza todas las preguntas | La partida termina en FINALIZADA |
| 3 | La partida finalizada | Cualquiera consulta el estado | Ve el ranking de los 3 y un ganador |

Prueba: `test_hu01_profesor_crea_partida_y_tres_estudiantes_juegan`

## HU-02 – Gana quien sabe
**Como** estudiante **quiero** que quien responde bien gane **para** que el juego sea justo.

| # | Dado | Cuando | Entonces |
|---|---|---|---|
| 1 | Una partida con dos estudiantes | Uno acierta todas y el otro falla todas | El que acierta es el ganador y el otro tiene 0 puntos |
| 2 | Un estudiante que acierta seguido | Consulta su marcador | Su racha es igual al número de aciertos seguidos |

Prueba: `test_hu02_gana_quien_responde_bien`

## HU-03 – Una sola respuesta por pregunta
**Como** estudiante **quiero** que nadie pueda responder dos veces **para** que nadie haga trampa.

| # | Dado | Cuando | Entonces |
|---|---|---|---|
| 1 | Una pregunta abierta y un estudiante que ya respondió | Intenta responder otra vez | Recibe un error 409 y su puntaje no cambia |
| 2 | Una pregunta ya cerrada | Un estudiante intenta responder | Recibe un error 409 |

Prueba: `test_hu03_no_se_puede_responder_dos_veces`

## HU-04 – Solo el profesor controla su partida
**Como** profesor **quiero** que solo yo pueda iniciar y avanzar mi partida **para** que un
estudiante no la sabotee.

| # | Dado | Cuando | Entonces |
|---|---|---|---|
| 1 | Una partida en LOBBY | Alguien sin el token del anfitrión intenta iniciarla | Recibe 403 y la partida sigue en LOBBY |
| 2 | Una partida iniciada | Alguien con un token falso intenta avanzar | Recibe 403 y la pregunta no cambia |

Prueba: `test_hu04_solo_el_profesor_controla_la_partida`

## HU-05 – Ver la partida en vivo
**Como** estudiante **quiero** ver en mi pantalla, sin recargar, cuando alguien se une y cuando
empieza la pregunta **para** seguir el juego en vivo.

| # | Dado | Cuando | Entonces |
|---|---|---|---|
| 1 | Un estudiante conectado por WebSocket al PIN | Otro estudiante se une | Recibe el nuevo estado con ambos nombres |
| 2 | El mismo estudiante conectado | El profesor inicia la partida | Recibe el estado PREGUNTA sin la respuesta correcta |

Prueba: `test_hu05_ver_la_partida_en_vivo`
