# API de TestQuiz – El Saboteador

Base local: `http://127.0.0.1:8000`. La especificación interactiva está disponible en `/docs`.

## Partidas

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| `GET` | `/salud` | Público | Estado y versión del servicio. |
| `POST` | `/api/partidas` | Público | Crea una partida; acepta opcionalmente `{"categoria":"pruebas"}` o `{"categoria":"cultura"}`. Devuelve `pin` y `token_host`. |
| `GET` | `/api/partidas/{pin}` | Público | Estado público de la partida. El PIN debe tener seis dígitos. |
| `POST` | `/api/partidas/{pin}/jugadores` | Público | Une un jugador con `{"nombre":"..."}`. |
| `POST` | `/api/partidas/{pin}/iniciar` | Anfitrión | Inicia la partida; requiere `X-Host-Token`. |
| `POST` | `/api/partidas/{pin}/siguiente` | Anfitrión | Cierra la pregunta o avanza la partida; requiere `X-Host-Token`. |
| `POST` | `/api/partidas/{pin}/respuestas` | Público | Envía `{"nombre":"...","opcion":0}`; la opción es un entero de 0 a 3. |
| `GET` | `/api/partidas/{pin}/jugadores/{nombre}` | Público | Consulta puntos, racha, tiempo y posición del jugador. |
| `WS` | `/ws/{pin}` | Público | Envía el estado inicial y actualizaciones `{"tipo":"estado","datos":...}`. Un PIN inexistente cierra con código `4404`. |

Los errores REST usan `{"detail":"..."}`. Entre los estados habituales están `403` (token
inválido), `404` (PIN o recurso inexistente), `409` (acción no válida para el estado actual) y
`422` (entrada inválida).

## Panel de administración

Todas las rutas `/api/admin` requieren el encabezado `X-Admin-Token: <ADMIN_TOKEN>`.
Si `PERMITIR_SABOTAJE=false`, el panel responde `404`; sin token válido responde `403`.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/admin/sabotajes` | Catálogo de mutantes y estado activo. |
| `POST` | `/api/admin/sabotajes/reparar` | Desactiva todos los mutantes. |
| `POST` | `/api/admin/sabotajes/{clave}/activar` | Activa un mutante del catálogo. |
| `POST` | `/api/admin/sabotajes/{clave}/desactivar` | Desactiva un mutante. |
| `POST` | `/api/admin/pruebas` | Ejecuta los niveles de pruebas permitidos y devuelve el tablero de dominó. |
| `GET` | `/api/admin/partidas` | Lista las partidas activas. |
| `GET` | `/api/admin/partidas/{pin}/impacto` | Devuelve la evaluación de impacto real y mostrada por jugador y respuesta. |

## Variables de entorno

| Variable | Predeterminado | Uso |
|---|---|---|
| `ADMIN_TOKEN` | vacío | Protege el panel; vacío bloquea todo acceso administrativo. |
| `PERMITIR_SABOTAJE` | `true` | Habilita o oculta el panel del Saboteador. |
| `MAX_PARTIDAS` | `500` | Máximo de partidas simultáneas. |
| `PARTIDA_TTL_MINUTOS` | `30` | Tiempo de expiración de partidas inactivas. |
| `PORT` | `8000` | Puerto del servidor (Render lo proporciona al desplegar). |
| `APP_URL` | no definida | URL base para las pruebas de humo contra el servicio desplegado. |

## Operación CI / despliegue

El despliegue requiere el secreto GitHub `RENDER_DEPLOY_HOOK` y la variable de repositorio
`APP_URL`. La compuerta de SonarCloud se dejó pendiente para el final; por ello, el reporte de
predespliegue actual devuelve **NO DESPLEGAR** mientras no exista evidencia de un Quality Gate
aprobado. No se debe configurar el despliegue como automático al margen de esa compuerta.
