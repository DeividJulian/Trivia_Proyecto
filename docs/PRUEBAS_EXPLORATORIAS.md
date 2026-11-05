# Pruebas exploratorias

Sesiones manuales con un objetivo (charter) y tiempo limitado, hechas el 2026-11-04 contra el
servidor local (`uvicorn app.main:app`) con `curl` y un script de WebSockets, **después** de que
la suite automatizada ya pasaba (152 pruebas en verde, 99 % de cobertura).

## Por qué hacerlas si ya hay pruebas automatizadas

- **Mito: "con automatización ya no hay pruebas manuales".** Las pruebas automatizadas solo
  verifican lo que alguien pensó de antemano. Las tres sesiones encontraron **3 defectos reales**
  (DEF-008, DEF-009 y DEF-010) en un código con 99 % de cobertura y todo en verde. La cobertura dice
  qué líneas se ejecutaron, no qué entradas se probaron.
- **Falacia: "cualquier clic es testing".** Explorar no es usar la aplicación al azar: cada sesión
  tiene un objetivo, un tiempo, técnicas (valores límite, tipos inesperados, orden incorrecto,
  fallos de red), notas y resultados. Cada hallazgo se convierte en DEF y en una prueba automatizada,
  para que no vuelva (regresión).

## Sesión 1 – Entradas de los jugadores

| Campo | Valor |
|---|---|
| Objetivo | Explorar la validación de `nombre` y `opcion` con valores límite y tipos inesperados, para descubrir entradas que el juego acepte sin deber hacerlo |
| Tiempo | 30 minutos |
| Técnicas | Valores límite (0, 1, 20 y 21 caracteres; opción -1, 0, 3, 4), solo espacios, tabulador, Unicode y emoji, HTML, tipos equivocados (`123`, `true`, `"2"`, `1.0`), JSON roto y campos extra |
| Hallazgos | 1) `"   "` y `"\t"` → **409** en vez de 422 → **DEF-008**. 2) `"opcion": true` → **200 y 1000 puntos** (se convierte en 1); `"2"` y `1.0` también se aceptaban → **DEF-009**. 3) `"Ñandú 😀"` dio 400 con curl en la consola de Windows; con un cliente Python dio 201: era un problema de codificación de la consola, **no del servidor** (falso positivo, sin DEF). 4) Nombre con `<script>` (25 caracteres) → 422 por longitud; el back no renderiza HTML, pero el front deberá escapar los nombres (nota para el front). 5) Campo extra `admin: true` → se ignora (correcto). |
| Defectos creados | DEF-008, DEF-009 |

## Sesión 2 – Flujo de la partida fuera de orden

| Campo | Valor |
|---|---|
| Objetivo | Explorar qué pasa si el anfitrión o los jugadores hacen las acciones en un orden inesperado o con PIN y tokens raros |
| Tiempo | 30 minutos |
| Técnicas | Transiciones de estado inválidas, repetición rápida (25 `siguiente` seguidos), respuestas después de terminar, PIN con letras, corto y de 300 dígitos, token de otra partida y con espacios |
| Hallazgos | 1) `siguiente` en LOBBY → 409 (correcto). 2) 25 `siguiente` seguidos recorren las 10 preguntas y terminan en FINALIZADA sin error 500 (correcto). 3) Responder en FINALIZADA → 409 (correcto). 4) Token de otra partida y token con espacios → 403 (correcto). 5) PIN `abc` → 404 y **PIN de 300 dígitos → 404 que repite los 300 caracteres** → **DEF-010**. Al corregirlo, la re-ejecución mostró que el 422 estándar también repetía la entrada (segunda corrección del mismo DEF). |
| Defectos creados | DEF-010 |

## Sesión 3 – Tiempo real y robustez

| Campo | Valor |
|---|---|
| Objetivo | Explorar si la difusión por WebSocket sobrevive a desconexiones bruscas y a una partida llena |
| Tiempo | 20 minutos |
| Técnicas | 30 sockets en la misma partida, 15 cerrados de forma brusca (sin cierre WebSocket), acción posterior; partida con 50 jugadores y el 51; WebSocket con PIN inexistente; 5 respuestas seguidas del mismo jugador |
| Hallazgos | 1) Tras cerrar 15 sockets de golpe, unirse respondió 201 y **los 15 sockets vivos recibieron el estado** (correcto). 2) Jugador 51 → 409 "La partida está llena: máximo 50 jugadores" (correcto). 3) WebSocket con PIN inexistente → cierre 4404 con motivo (correcto). 4) 5 respuestas seguidas → `[200, 409, 409, 409, 409]` (correcto). 5) Sin errores ni trazas en el log del servidor. 6) El cliente de prueba tardaba unos 2 s por petición: `localhost` en Windows intenta IPv6 primero; con `127.0.0.1` desaparece. Es del cliente, **no del servidor** (nota para las pruebas de rendimiento). |
| Defectos creados | Ninguno |

## Resultado

| Sesión | Minutos | Defectos | Falsos positivos |
|---|---|---|---|
| 1 – Entradas | 30 | DEF-008, DEF-009 | 1 (codificación de la consola) |
| 2 – Flujo | 30 | DEF-010 | 0 |
| 3 – Robustez | 20 | 0 | 1 (IPv6 del cliente) |

Los tres defectos quedaron cubiertos por `tests/sistema/test_validacion_entradas.py`.
