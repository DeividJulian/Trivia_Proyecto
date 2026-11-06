# Reporte de defectos

## Ciclo de vida del defecto

```
Nuevo -> Asignado -> En corrección -> Corregido -> Confirmado (re-ejecución) -> Cerrado
                          \-> Riesgo aceptado (falso positivo o riesgo justificado)
```

Cada defecto sigue el ciclo de mantenimiento visto en clase:
**detonante → intervención → confirmación → análisis de impacto → regresión**.

- La corrección va en su propio commit: `fix(<módulo>): <qué se corrigió> (DEF-00X)`.
- Un falso positivo se marca **Riesgo aceptado**, con justificación y `# noqa` con el código exacto
  de la regla. Nunca se desactivan reglas en bloque.
- No se cambia un umbral ni se borra una prueba para que algo pase.

## Plantilla

```markdown
### DEF-00X – Título corto
| Campo | Valor |
|---|---|
| Detectado por | Herramienta (pytest / Ruff / SonarLint / SonarQube / Trivy) y nivel |
| Severidad | Crítica / Alta / Media / Baja |
| Pasos para reproducir | 1. … 2. … |
| Resultado esperado / obtenido | … |
| Causa encontrada (debugging) | … |
| Corrección | Commit `fix(...)` |
| Re-ejecución (confirmación) | Comando y salida |
| Análisis de impacto | Módulos afectados |
| Regresión ejecutada | Comando y salida |
| Estado | Cerrado / Riesgo aceptado / Abierto |
```

## Defectos registrados

### DEF-001 – Ruff S101 marca los `assert` de las pruebas
| Campo | Valor |
|---|---|
| Detectado por | Ruff, regla S101 (análisis estático, pre-commit) sobre el código de pruebas |
| Severidad | Baja |
| Pasos para reproducir | 1. Crear `tests/sistema/test_salud.py` con `assert`. 2. `ruff check .` |
| Resultado esperado / obtenido | Esperado: sin hallazgos. Obtenido: `S101 Use of assert detected` (2 hallazgos) |
| Causa encontrada (debugging) | S101 existe porque `python -O` elimina los `assert` en producción. En pytest el `assert` **es** la verificación y las pruebas nunca se ejecutan con `-O`. Es un falso positivo para `tests/`. |
| Corrección | Commit `fix(ruff): S101 en tests es riesgo aceptado, solo para tests/ (DEF-001)`: `per-file-ignores` de **solo S101** y **solo en `tests/**`**. `app/` sigue revisado con todas las reglas (en `app/` no hay `assert`). |
| Re-ejecución (confirmación) | `ruff check .` → `All checks passed!` |
| Análisis de impacto | Solo la carpeta `tests/`. |
| Regresión ejecutada | `pytest -q` → `1 passed` |
| Estado | **Riesgo aceptado** |

### DEF-002 – Aviso de obsolescencia de `httpx` en el TestClient
| Campo | Valor |
|---|---|
| Detectado por | pytest (resumen de warnings), nivel sistema |
| Severidad | Baja |
| Pasos para reproducir | 1. `pytest -q` |
| Resultado esperado / obtenido | Esperado: sin avisos. Obtenido: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` |
| Causa encontrada (debugging) | La versión de Starlette que trae FastAPI anuncia que su TestClient migrará de `httpx` a `httpx2`. Solo afecta a las pruebas: el servidor no usa el TestClient. |
| Corrección | Ninguna por ahora. El aviso **no** se oculta con filtros; se migrará a `httpx2` como mantenimiento adaptativo cuando se actualicen las dependencias de desarrollo. |
| Re-ejecución (confirmación) | `pytest -q` → `1 passed, 1 warning` |
| Análisis de impacto | Solo herramientas de prueba (`tests/sistema`, `tests/aceptacion`). |
| Regresión ejecutada | — |
| Estado | **Riesgo aceptado** (seguimiento como mantenimiento adaptativo) |

### DEF-003 – El hook `ruff` de pre-commit es un alias heredado
| Campo | Valor |
|---|---|
| Detectado por | pre-commit (`pre-commit run --all-files`), shift-left |
| Severidad | Baja |
| Pasos para reproducir | 1. `pre-commit run --all-files` |
| Resultado esperado / obtenido | Esperado: `ruff check ... Passed`. Obtenido: `ruff (legacy alias) ... Passed` |
| Causa encontrada (debugging) | En ruff-pre-commit v0.17 el id del hook es `ruff-check`; `ruff` se conserva solo por compatibilidad y puede desaparecer. |
| Corrección | Commit `fix(pre-commit): usa el hook ruff-check en vez del alias heredado ruff (DEF-003)` |
| Re-ejecución (confirmación) | `pre-commit run --all-files` → `ruff check ... Passed`, `ruff format ... Passed` |
| Análisis de impacto | Solo el flujo local de commits. |
| Regresión ejecutada | `pytest -q` → `1 passed` |
| Estado | **Cerrado** |

### DEF-004 – Ruff S105 confunde un valor de prueba con una contraseña
| Campo | Valor |
|---|---|
| Detectado por | Ruff, regla S105 (pre-commit) en `tests/componente/test_config.py` |
| Severidad | Baja |
| Pasos para reproducir | 1. `ruff check tests/componente/test_config.py` |
| Resultado esperado / obtenido | Esperado: sin hallazgos. Obtenido: `S105 Possible hardcoded password assigned to: "admin_token"` en la línea `assert config.admin_token == "secreto"` |
| Causa encontrada (debugging) | S105 marca cualquier literal comparado con un nombre que parece credencial. Aquí es un valor inventado que la prueba pone con `monkeypatch.setenv` para comprobar que se lee del entorno; no es un secreto real ni se usa fuera de la prueba. |
| Corrección | `# noqa: S105` **solo en esa línea**, con el motivo y el número del DEF. No se ignora S105 en ningún otro lugar. |
| Re-ejecución (confirmación) | `ruff check .` → `All checks passed!` |
| Análisis de impacto | Solo `tests/componente/test_config.py`. |
| Regresión ejecutada | `pytest -q` → `8 passed` |
| Estado | **Riesgo aceptado** |

### DEF-005 – Ruff S105/S106 en los tokens usados por las pruebas de sistema
| Campo | Valor |
|---|---|
| Detectado por | Ruff, reglas S105 y S106 (pre-commit) en `tests/sistema/test_seguridad.py` |
| Severidad | Baja |
| Pasos para reproducir | 1. Escribir `crear_app(config=Configuracion(admin_token="demo"))` en una prueba. 2. `ruff check .` |
| Resultado esperado / obtenido | Esperado: sin hallazgos. Obtenido: 5 hallazgos `S106 Possible hardcoded password assigned to argument: "admin_token"` / `S105` |
| Causa encontrada (debugging) | Las pruebas necesitan un token conocido para crear la app; cada literal repetido parece una credencial para Ruff. Repetir `# noqa` en cada prueba esconde el motivo y ensucia el código. |
| Corrección | Se crea `tests/valores_prueba.py` con `TOKEN_ADMIN_PRUEBA` y `OTRO_TOKEN_PRUEBA`, cada uno con **un** `# noqa: S105` justificado. Las pruebas usan esas constantes y ya no tienen literales con aspecto de credencial. |
| Re-ejecución (confirmación) | `ruff check .` → `All checks passed!` |
| Análisis de impacto | Solo `tests/`. Las pruebas futuras del panel admin reutilizan las mismas constantes. |
| Regresión ejecutada | `pytest -q` → `12 passed` |
| Estado | **Riesgo aceptado** |

### DEF-006 – Ruff N818 pide el sufijo "Error" en la excepción base
| Campo | Valor |
|---|---|
| Detectado por | Ruff, regla N818 (pre-commit) en `app/dominio/errores.py` |
| Severidad | Baja |
| Pasos para reproducir | 1. `ruff check app` |
| Resultado esperado / obtenido | Esperado: sin hallazgos. Obtenido: `N818 Exception name ErrorPartida should be named with an Error suffix` |
| Causa encontrada (debugging) | N818 asume nombres en inglés (`GameError`). En español el sustantivo va primero: `ErrorPartida`. El nombre es parte del lenguaje del dominio usado en el plan y en la API, y comunica bien que es una excepción. Solo se marca la clase que hereda directamente de `Exception`. |
| Corrección | `# noqa: N818` **solo** en la línea de `class ErrorPartida`, con el motivo. La regla N818 sigue activa en todo el proyecto. |
| Re-ejecución (confirmación) | `ruff check .` → `All checks passed!` |
| Análisis de impacto | Solo `app/dominio/errores.py`. |
| Regresión ejecutada | `pytest -q` → `12 passed` |
| Estado | **Riesgo aceptado** |

### DEF-007 – Un JSON de preguntas mal formado no dice qué archivo falló
| Campo | Valor |
|---|---|
| Detectado por | pytest, nivel componente: `tests/componente/test_preguntas.py::test_json_mal_formado_indica_el_archivo` |
| Severidad | Media (al arrancar con un banco dañado, el administrador no sabe qué archivo corregir) |
| Pasos para reproducir | 1. Crear `roto.json` con `[{ esto no es json`. 2. `cargar_preguntas(ruta="roto.json")` |
| Resultado esperado / obtenido | Esperado: `ValueError` que nombre `roto.json`. Obtenido: `Expecting property name enclosed in double quotes: line 1 column 4 (char 3)` sin el nombre del archivo |
| Causa encontrada (debugging) | `cargar_preguntas` validaba la estructura y cada pregunta, pero `json.load` estaba fuera del `try`: el `JSONDecodeError` (subclase de `ValueError`) salía con el mensaje crudo de la librería estándar. |
| Corrección | Commit `fix(preguntas): el error de JSON mal formado indica el archivo, la línea y la columna (DEF-007)` |
| Re-ejecución (confirmación) | `pytest tests/componente/test_preguntas.py::test_json_mal_formado_indica_el_archivo` → `1 passed` |
| Análisis de impacto | `preguntas` → `partida` (la partida recibe las preguntas cargadas). El cambio solo afecta al camino de error; las cargas válidas no cambian. |
| Regresión ejecutada | `pytest -m componente` → `30 passed`; suite completa `pytest -q` → `35 passed` |
| Estado | **Cerrado** |

### DEF-008 – Un nombre solo con espacios responde 409 en vez de 422
| Campo | Valor |
|---|---|
| Detectado por | Prueba exploratoria manual (sesión 1, `docs/PRUEBAS_EXPLORATORIAS.md`), nivel sistema |
| Severidad | Baja |
| Pasos para reproducir | 1. `POST /api/partidas`. 2. `POST /api/partidas/{pin}/jugadores` con `{"nombre": "   "}` |
| Resultado esperado / obtenido | Esperado: 422 (entrada inválida). Obtenido: 409 `El nombre debe tener entre 1 y 20 caracteres.` |
| Causa encontrada (debugging) | `UnirseEntrada` validaba `min_length=1` **antes** de quitar espacios: `"   "` mide 3 y pasaba. El dominio lo recortaba y lo rechazaba como `ErrorPartida`, que la API traduce a 409 (conflicto de estado). |
| Corrección | Commit `fix(api): un nombre solo con espacios es entrada inválida (422), no conflicto (DEF-008)`: tipo `Nombre` con `strip_whitespace=True` antes de validar la longitud. |
| Re-ejecución (confirmación) | `pytest tests/sistema/test_validacion_entradas.py -k espacios` → `3 passed` (`docs/evidencias/DEF-008-despues.txt`) |
| Análisis de impacto | API (`esquemas.py`) → Partida (recibe el nombre ya recortado). La regla del dominio no cambia. |
| Regresión ejecutada | `pytest -m "api or partida"` → `90 passed`; suite completa → `169 passed` |
| Estado | **Cerrado** |

### DEF-009 – `"opcion": true` se acepta como la opción 1 y suma puntos
| Campo | Valor |
|---|---|
| Detectado por | Prueba exploratoria manual (sesión 1), nivel sistema; confirmado con TestClient |
| Severidad | **Media** (un cliente mal hecho o malicioso responde con un valor que no es una opción y obtiene 1000 puntos) |
| Pasos para reproducir | 1. Crear partida, unirse e iniciar. 2. `POST /respuestas` con `{"nombre": "Ana", "opcion": true}` |
| Resultado esperado / obtenido | Esperado: 422. Obtenido: 200 `{"puntos": 1000, ...}` (la correcta de la 1.ª pregunta es 1). También se aceptaban `"2"` y `1.0`. |
| Causa encontrada (debugging) | Pydantic v2 en modo *lax* convierte `true` → 1, `"2"` → 2 y `1.0` → 1 en un campo `int`. |
| Corrección | Commit `fix(api): la opción solo acepta enteros; true ya no cuenta como la opción 1 (DEF-009)`: `Field(..., strict=True)`. |
| Re-ejecución (confirmación) | `pytest tests/sistema/test_validacion_entradas.py -k entero_estricto` → `4 passed` (`DEF-009-despues.txt`) |
| Análisis de impacto | API → Partida → Puntaje → Ranking: una opción mal interpretada cambia puntos y posiciones. |
| Regresión ejecutada | `pytest -m "api or partida or puntaje"` → `110 passed`; suite completa → `169 passed` |
| Estado | **Cerrado** |

### DEF-010 – El PIN no se valida y los errores repiten la entrada recibida
| Campo | Valor |
|---|---|
| Detectado por | Prueba exploratoria manual (sesión 2), nivel sistema |
| Severidad | Baja (seguridad: reflejo de entradas arbitrarias en las respuestas) |
| Pasos para reproducir | 1. `GET /api/partidas/` seguido de 300 nueves |
| Resultado esperado / obtenido | Esperado: 422 corto, sin la entrada. Obtenido: 404 `No existe una partida con el PIN 9999…` (300 caracteres repetidos) |
| Causa encontrada (debugging) | El parámetro `pin` era un `str` libre y el mensaje de `PartidaNoEncontrada` lo incluye. Al validar el formato apareció una segunda causa: el 422 estándar de FastAPI devuelve el campo `input` con la entrada completa. |
| Corrección | 1) `fix(api): el PIN se valida como 6 dígitos (422) y no se repite en la respuesta (DEF-010)`: `Path(pattern=r"^\d{6}$")` y, en el WebSocket, cierre 4404 con un mensaje fijo. 2) `fix(api): las respuestas 422 no repiten la entrada recibida (DEF-010)`: manejador propio de `RequestValidationError` que devuelve solo `type`, `loc` y `msg`. |
| Re-ejecución (confirmación) | **1.ª confirmación: falló** (`assert 455 < 400`, el 422 traía la entrada). Tras la 2.ª corrección: `5 passed` (`DEF-010-despues.txt`). Muestra por qué la re-ejecución es obligatoria: la primera corrección parecía suficiente. |
| Análisis de impacto | Todas las rutas con `{pin}` y todas las respuestas 422 de la API. |
| Regresión ejecutada | `pytest -m api` → `63 passed`; suite completa → `169 passed` |
| Estado | **Cerrado** |

### DEF-011 – El bono por velocidad se suma a respuestas incorrectas (efecto dominó de la SC-001)
| Campo | Valor |
|---|---|
| Detectado por | pytest en 3 niveles: **componente** (`test_puntaje.py::test_respuesta_incorrecta_suma_0_y_reinicia_la_racha`), **sistema** (`test_api.py::test_partida_completa_de_extremo_a_extremo`) y **aceptación** (`test_historias.py::test_hu02_gana_quien_responde_bien`). GitHub Actions en rojo: [run 41956121926](https://github.com/DeividJulian/Trivia_Proyecto/actions/runs/41956121926) |
| Severidad | **Crítica** (el ranking deja de ser justo: quien responde rápido pero mal suma hasta 500 puntos por pregunta) |
| Pasos para reproducir | 1. `git checkout v2-cambio-con-error`. 2. `pytest -q` → 3 failed, 175 passed. 3. `calcular_puntos(False, 1.0, 20.0, 4)` devuelve `(475, 0)` |
| Resultado esperado / obtenido | Esperado: una respuesta incorrecta vale 0. Obtenido: vale el bono por velocidad (475 con 1 s de 20; 1425 acumulados en la prueba de sistema; 1500 en la de aceptación) |
| Causa encontrada (debugging) | Traza línea por línea con `sys.settrace` (`docs/evidencias/DEF-011-depuracion.txt`): el bono se calcula en la línea 47 **antes** de comprobar si la respuesta es correcta, y la línea 49 devuelve `return bono, nueva_racha` en la rama `if not opcion_correcta`. Las pruebas nuevas del bono solo probaban respuestas correctas, por eso pasaban. |
| Corrección | Commit `fix(puntaje): el bono solo aplica a respuestas correctas (DEF-011)` |
| Re-ejecución (confirmación) | Solo las 3 que fallaron: `pytest -v tests/componente/test_puntaje.py::test_respuesta_incorrecta_suma_0_y_reinicia_la_racha tests/sistema/test_api.py::test_partida_completa_de_extremo_a_extremo tests/aceptacion/test_historias.py::test_hu02_gana_quien_responde_bien` → `3 passed`. Depuración repetida: `calcular_puntos(False, 1.0, 20.0, 4)` → `(0, 0)`. Se agregó `test_respuesta_incorrecta_y_rapida_no_recibe_bono` (el caso que faltaba en las pruebas nuevas). Evidencia: `DEF-011-despues.txt` |
| Análisis de impacto | Puntaje → Racha (no afectada: la racha se reinicia bien) → **Ranking** (orden incorrecto) → **Partida** (acumula puntos falsos) → **API** (expone puntos y ganador falsos). Ver `SOLICITUD_CAMBIO_001.md`. |
| Regresión ejecutada | Selectiva por impacto: `pytest -m "puntaje or ranking or partida or api"` → `127 passed, 51 deselected`. Suite completa: `pytest -q` → `178 passed`. GitHub Actions en verde en `v3-corregido`. |
| Estado | **Cerrado** |

### DEF-012 – Ruff E402 y S603 en el script de regresión por impacto
| Campo | Valor |
|---|---|
| Detectado por | Ruff (pre-commit), reglas E402 y S603, en `scripts/regresion_por_impacto.py` |
| Severidad | Baja |
| Pasos para reproducir | `ruff check scripts --ignore-noqa` (`docs/evidencias/DEF-012-antes.txt`) |
| Resultado esperado / obtenido | Esperado: sin hallazgos. Obtenido: 1 × E402 (import después de modificar `sys.path`) y 2 × S603 (`subprocess` con posible entrada no confiable) |
| Causa encontrada (debugging) | E402: el script se ejecuta como `python scripts\regresion_por_impacto.py`, así que necesita agregar la raíz del repo a `sys.path` **antes** de importar `app`. S603: el script llama a `git diff` y a `pytest`; los comandos son fijos, sin `shell=True`, con la ruta absoluta de git (`shutil.which`) y `sys.executable`; el único dato variable es el nombre de la rama base que escribe el propio desarrollador. |
| Corrección | Riesgo aceptado: `# noqa: E402` y `# noqa: S603` **solo en esas 3 líneas**, cada uno con su motivo. Se evitó S607 usando rutas absolutas. |
| Re-ejecución (confirmación) | `ruff check scripts` → `All checks passed!`; `python scripts/regresion_por_impacto.py --solo-ver` funciona (`DEF-012-despues.txt`) |
| Análisis de impacto | Solo herramientas de calidad (`scripts/`). No afecta al servidor. |
| Regresión ejecutada | `pytest -q` → `203 passed` |
| Estado | **Riesgo aceptado** |

### DEF-013 – Ruff S314, S603 y E402 en el ejecutor de pruebas y en verificar_mutantes
| Campo | Valor |
|---|---|
| Detectado por | Ruff (pre-commit), reglas S314, S603 y E402, en `app/calidad/ejecutor.py` y `scripts/verificar_mutantes.py` |
| Severidad | Baja |
| Pasos para reproducir | `ruff check app/calidad scripts --ignore-noqa` (`docs/evidencias/DEF-013-antes.txt`) |
| Resultado esperado / obtenido | Esperado: sin hallazgos. Obtenido: S314 (parsear XML con `xml.etree`, vulnerable a XML malicioso), S603 (`subprocess`) y E402 (import tras ajustar `sys.path`) |
| Causa encontrada (debugging) | S314: el XML lo genera **nuestro propio** pytest en una carpeta temporal creada por el ejecutor (`tempfile.TemporaryDirectory`); nunca llega desde la red ni desde el usuario. S603: se ejecuta `sys.executable -m pytest` con argumentos fijos; los únicos datos variables son claves de sabotaje validadas contra el catálogo y niveles validados por Pydantic (`Literal`), así que el panel no permite pasar argumentos libres a pytest (probado en `test_no_acepta_argumentos_libres_de_pytest`). E402: igual que en DEF-012. |
| Corrección | Riesgo aceptado con `# noqa` solo en esas líneas, cada uno con su motivo. No se agregó `defusedxml` porque no hay entrada externa; si algún día el XML viniera de fuera, se cambia a `defusedxml` (anotado como mantenimiento preventivo). |
| Re-ejecución (confirmación) | `ruff check app/calidad scripts` → `All checks passed!` (`DEF-013-despues.txt`) |
| Análisis de impacto | Calidad (ejecutor) → Admin (`POST /api/admin/pruebas`). |
| Regresión ejecutada | `pytest -q` → `241 passed`; `python scripts/verificar_mutantes.py` → 6/6 detectados |
| Estado | **Riesgo aceptado** |

### DEF-014 – Conexiones reiniciadas tras 5 s sin actividad (keep-alive de uvicorn)
| Campo | Valor |
|---|---|
| Detectado por | Locust, prueba de estrés local (`punto_quiebre.py`), nivel sistema, **no funcional** |
| Severidad | Media (un profesor que espera unos segundos en el lobby puede recibir un error al iniciar la partida) |
| Pasos para reproducir | 1. `uvicorn app.main:app --port 8000` (sin opciones). 2. `locust -f performance\punto_quiebre.py --host http://127.0.0.1:8000 --headless ...`. 3. Revisar `quiebre_local_failures.csv` |
| Resultado esperado / obtenido | Esperado: 0 fallos de conexión. Obtenido: 21 fallos en `POST /iniciar` (`ConnectionResetError 10054`, `ConnectionAbortedError 10053`, `RemoteDisconnected`) (`DEF-014-antes.txt`) |
| Causa encontrada (debugging) | Los fallos aparecían **solo** en `POST /iniciar`, la única petición que el presentador hace tras esperar 5 s sin enviar nada. uvicorn cierra las conexiones inactivas a los **5 s** (`--timeout-keep-alive` por defecto) y el cliente reutilizaba esa conexión justo cuando el servidor la cerraba (carrera del keep-alive). |
| Corrección | Ejecutar uvicorn con `--timeout-keep-alive 75` (mayor que las esperas normales de un cliente y que el keep-alive de los balanceadores habituales). Se aplica en el `CMD` del Dockerfile (Fase 13) y en el README. |
| Re-ejecución (confirmación) | Con el servidor nuevo verificado (`Get-NetTCPConnection`): carga 50 usuarios → 0 fallos; estrés hasta 1000 usuarios → 0 fallos (`DEF-014-despues.txt`). **Nota:** una primera re-ejecución no fue válida porque el servidor nuevo no arrancó (puerto ocupado por el anterior) y las pruebas corrieron contra el viejo; se detectó por el código de salida 3 y se repitió. |
| Análisis de impacto | Configuración del servidor (despliegue): API completa. No cambia el código. |
| Regresión ejecutada | `pytest -q` → `254 passed`; carga local: RNF-01 y RNF-02 cumplen |
| Estado | **Cerrado** (la configuración queda fija en el Dockerfile de la Fase 13) |

### DEF-015 – El script de carga avanza partidas que no se iniciaron (409 falsos)
| Campo | Valor |
|---|---|
| Detectado por | Locust (fallos `409` en `POST /siguiente`), revisando la causa de DEF-014 |
| Severidad | Baja (defecto del **script de prueba**: inflaba la tasa de fallos) |
| Pasos para reproducir | Igual que DEF-014: 21 × `409 Conflict` en `POST /siguiente` |
| Causa encontrada (debugging) | En `Presentador.dirigir_partida`, si `POST /iniciar` fallaba por la conexión (status 0), el código seguía el bucle y llamaba a `/siguiente` sobre una partida en LOBBY → 409. Coincidía 1 a 1 con los fallos de `/iniciar`. |
| Corrección | Commit `fix(rendimiento): el presentador no avanza la partida si iniciar falló (DEF-015)` |
| Re-ejecución (confirmación) | Sin `409` en `/siguiente` en las corridas siguientes (`DEF-015-despues.txt`) |
| Análisis de impacto | Solo `performance/locustfile.py` (y `punto_quiebre.py`, que usa sus usuarios). |
| Regresión ejecutada | `pytest -q` → `254 passed` |
| Estado | **Cerrado** |

### DEF-016 – El script de carga agota el cupo de 500 partidas con partidas vacías
| Campo | Valor |
|---|---|
| Detectado por | Locust: 1246 × `409` en `POST /api/partidas` ("Se alcanzó el máximo de 500 partidas") en la segunda corrida de estrés (`DEF-016-antes.txt`) |
| Severidad | Media (falseaba el punto de quiebre: la prueba "quebraba" en 800 usuarios por el cupo, no por el rendimiento) |
| Pasos para reproducir | Estrés con el locustfile anterior contra un servidor con partidas de corridas previas |
| Causa encontrada (debugging) | Todos los jugadores se unían a la **última** partida publicada; con muchos presentadores, las demás quedaban vacías, el presentador las abandonaba (409 al iniciar) y creaba otra cada ~6 s. Las partidas abandonadas en LOBBY viven 30 min (`PARTIDA_TTL_MINUTOS`) y llenaron el cupo `MAX_PARTIDAS=500`. El límite del servidor funcionó como se diseñó (409 con mensaje claro). |
| Corrección | Commit `fix(rendimiento): los jugadores se reparten entre las partidas abiertas y el presentador no abandona la suya vacía (DEF-016)`. **Mejora preventiva propuesta** (no implementada): limpiar antes las partidas en LOBBY sin jugadores, para que nadie pueda agotar el cupo creando partidas vacías. |
| Re-ejecución (confirmación) | Estrés hasta 1000 usuarios: 0 × `409` en `POST /api/partidas`, 0 fallos (`DEF-016-despues.txt`) |
| Análisis de impacto | Script de carga. En el servidor: Gestor (cupo y limpieza), anotado como riesgo. |
| Regresión ejecutada | `pytest -q` → `254 passed` |
| Estado | **Cerrado** (riesgo del cupo anotado en `RESULTADOS_RENDIMIENTO.md`) |

### DEF-017 – La imagen Docker no podía ejecutar la suite (faltaba `performance/`)
| Campo | Valor |
|---|---|
| Detectado por | pytest sobre una copia con el contenido exacto de la imagen (nivel sistema, despliegue). Docker no está instalado en la máquina, así que se reprodujo copiando lo mismo que copia el Dockerfile. |
| Severidad | **Alta** (en producción, `POST /api/admin/pruebas` devolvería un tablero vacío: el modo Saboteador, eje de la exposición, no funcionaría) |
| Pasos para reproducir | 1. Copiar `pyproject.toml`, `app/`, `data/` y `tests/` a una carpeta vacía. 2. `pytest -q` → `2 errors during collection` (`DEF-017-antes.txt`) |
| Resultado esperado / obtenido | Esperado: la suite completa pasa dentro de la imagen. Obtenido: `ModuleNotFoundError: performance` en `test_umbrales.py` y `test_analizar_resultados.py` |
| Causa encontrada (debugging) | El `.dockerignore` excluía `performance/` completo y el Dockerfile no lo copiaba, pero dos pruebas de componente importan `performance.verificar_umbrales` y `performance.analizar_resultados`. |
| Corrección | Commit `fix(docker): la imagen incluye performance/ porque las pruebas lo importan; el panel no podía correr la suite (DEF-017)`: `COPY performance ./performance`; el `.dockerignore` solo excluye `performance/resultados/`. |
| Re-ejecución (confirmación) | Copia corregida: `pytest -q` → `254 passed`; el ejecutor del panel con `empates_mal` arma el tablero (Ranking y Partida CAIDO) (`DEF-017-despues.txt`). Confirmado después con Docker real: `docker build` y la suite dentro del contenedor (Bloque 1, ver DEF-026), y en cada ejecución del job de Trivy en el CI. |
| Análisis de impacto | Despliegue → panel del Saboteador (`POST /api/admin/pruebas`). |
| Regresión ejecutada | `pytest -q` → `254 passed` |
| Estado | **Cerrado** |

### DEF-018 – Trivy: setuptools 70.3.0 (CVE-2025-47273, HIGH) dentro de pip
| Campo | Valor |
|---|---|
| Detectado por | Trivy 0.76.1 (`trivy rootfs --scanners vuln .venv/Lib/site-packages`), seguridad / dependencias |
| Severidad | Alta según Trivy; **real: baja** (ver causa) |
| Pasos para reproducir | `trivy rootfs --scanners vuln .venv/Lib/site-packages` → `setuptools 70.3.0`: CVE-2025-47273 (HIGH), CVE-2026-59890 (MEDIUM), GHSA-xmj3-9gf7-h52w (LOW) (`DEF-018-antes.txt`) |
| Causa encontrada (debugging) | `pip show setuptools` → no está instalado. El hallazgo sale del inventario de **pip 26.3** (`pip/_vendor/vendor.txt` y `bom.cdx.json`: `setuptools==70.3.0`): pip solo incluye `pkg_resources` de ese setuptools. La CVE-2025-47273 está en `setuptools.package_index`, que pip **no** incluye. Es un falso positivo en ejecución, pero la imagen `python:3.12-slim` también trae pip, así que el gate de `trivy image` del CI fallaría por lo mismo. `trivy fs` del repositorio y `trivy config` del Dockerfile salieron limpios (0 HIGH/CRITICAL, 0 secretos, 0 malas configuraciones). |
| Corrección | Mantenimiento **adaptativo/preventivo**: commit `fix(docker): la imagen final no incluye pip ... (DEF-018)`: tras instalar las dependencias se desinstala pip (la app no lo usa en ejecución y se reduce la superficie de ataque). En el entorno local de desarrollo se acepta el riesgo: no se despliega y se actualizará pip cuando cambie su setuptools interno. |
| Re-ejecución (confirmación) | `trivy config Dockerfile` → 0; `trivy fs ... --severity HIGH,CRITICAL` → 0 (`DEF-018-despues.txt`). `trivy image` confirmado después en el CI: imagen sin pip y 0 HIGH/CRITICAL (run 42161113908 con Trivy 0.70.0 y run 42170687291 con Trivy 0.76.1). |
| Análisis de impacto | Solo la imagen (despliegue). La app no importa pip. |
| Regresión ejecutada | `pytest -q` → `254 passed`; `verificar_mutantes.py` → 6/6 |
| Estado | **Cerrado en la imagen** (confirmar en CI) / **Riesgo aceptado** en el entorno local |

### DEF-019 – Ternario anidado en el tablero de dominó de app/static/app.js (SonarLint S3358)
| Campo | Valor |
|---|---|
| Detectado por | SonarQube for IDE (SonarLint en VS Code), regla `javascript:S3358` ("Extract this nested ternary operation into an independent statement") |
| Severidad | Baja (code smell de mantenibilidad) |
| Pasos para reproducir | 1. Abrir `app/static/app.js` en VS Code con SonarLint activo. 2. Revisar la línea de formateo de `detalle.textContent` dentro del evento click de `adm-btn-pruebas`. |
| Resultado esperado / obtenido | Esperado: código sin operadores condicionales ternarios anidados. Obtenido: advertencia `javascript:S3358` en `detalle.textContent = datos.fallidas.length ? ... : datos.en_riesgo_por.length ? ... : ...` (`DEF-019-antes.txt` / `DEF-019-antes.png`) |
| Causa encontrada (debugging) | En `adm-btn-pruebas`, el texto descriptivo del estado de cada módulo en el tablero de dominó se formateaba mediante dos operadores ternarios anidados en una sola sentencia, lo cual reduce la legibilidad y viola el estándar de mantenibilidad S3358. |
| Corrección | Commit `fix(front): reemplaza el ternario anidado del tablero (DEF-019)`: se extrae la lógica a la función independiente `describirModulo(datos)` con sentencias `if/else` claras. |
| Re-ejecución (confirmación) | `node --check app/static/app.js` sin errores; sin advertencias en SonarLint (`DEF-019-despues.txt` / `DEF-019-despues.png`). |
| Análisis de impacto | Solo `app/static/app.js` (interfaz del tablero de administración). |
| Regresión ejecutada | `node --check app/static/app.js` OK; `pytest -q` → 259 passed. |
| Estado | **Cerrado** |

### DEF-020 – Ruff S314 señala el XML generado por las pruebas en el reporte predespliegue
| Campo | Valor |
|---|---|
| Detectado por | Ruff, regla S314 (análisis estático) en `scripts/reporte_predespliegue.py` |
| Severidad | Baja |
| Pasos para reproducir | 1. Analizar el script del reporte con `ruff check scripts/reporte_predespliegue.py`. |
| Resultado esperado / obtenido | Esperado: sin alertas. Obtenido: S314 en los dos `ET.parse` (`DEF-020-antes.txt`). |
| Causa encontrada (debugging) | Ruff no puede distinguir los informes XML locales y generados por pytest/coverage de XML externo no confiable. El reporte solo lee archivos producidos dentro del workspace por el propio pipeline. |
| Corrección | Riesgo aceptado, con `# noqa: S314` solo en las dos lecturas del XML generado por las herramientas del pipeline. No se desactiva la regla globalmente. |
| Re-ejecución (confirmación) | `ruff check ...` → `All checks passed!` (`DEF-020-despues.txt`). |
| Análisis de impacto | Solo el generador del reporte predespliegue. |
| Regresión ejecutada | `pytest -q tests/componente/test_reporte_predespliegue.py tests/integracion_sistemas/test_humo.py` → 6 passed, 2 skipped sin `APP_URL`. |
| Estado | **Riesgo aceptado** |

### DEF-021 – Sintaxis inválida al escapar separadores en el reporte predespliegue
| Campo | Valor |
|---|---|
| Detectado por | pytest, error de recolección de nivel componente |
| Severidad | Baja |
| Pasos para reproducir | Ejecutar `pytest -q tests/componente/test_reporte_predespliegue.py` antes de la corrección. |
| Resultado esperado / obtenido | Esperado: se recolectan y ejecutan las pruebas. Obtenido: `SyntaxError: f-string expression part cannot include a backslash` (`DEF-021-antes.txt`). |
| Causa encontrada (debugging) | El escapado Markdown con una barra invertida estaba dentro de una expresión f-string, sintaxis no permitida por Python. |
| Corrección | Se calcula el texto escapado antes de interpolarlo en el f-string. |
| Re-ejecución (confirmación) | `pytest -q tests/componente/test_reporte_predespliegue.py tests/integracion_sistemas/test_humo.py` → 8 passed, 2 skipped (`APP_URL` no configurada; `DEF-021-despues.txt`). |
| Análisis de impacto | Solo el formato de la tabla del reporte predespliegue. |
| Regresión ejecutada | Ruff check y format sobre los archivos nuevos; suite dirigida: 8 passed, 2 skipped. |
| Estado | **Cerrado** |

### DEF-022 – La ejecución directa del reporte no encuentra el módulo de rendimiento
| Campo | Valor |
|---|---|
| Detectado por | Ejecución manual del comando de generación de reporte en la integración CI |
| Severidad | Media (impide producir el artefacto de predespliegue) |
| Pasos para reproducir | Ejecutar `python scripts/reporte_predespliegue.py ...` desde la raíz del repositorio. |
| Resultado esperado / obtenido | Esperado: genera el Markdown con el veredicto. Obtenido: `ModuleNotFoundError: No module named 'performance'` (`DEF-022-antes.txt`). |
| Causa encontrada (debugging) | Al ejecutar un archivo por ruta, Python agrega `scripts/` a `sys.path`; la raíz del repositorio no estaba disponible para importar `performance`. |
| Corrección | Se agrega la raíz del repositorio a `sys.path` antes de importar el verificador de umbrales, evitando duplicarla cuando ya está presente. |
| Re-ejecución (confirmación) | Ejecución del CLI con evidencias locales: genera el reporte y sale con código 1 por Trivy no ejecutado y Sonar pendiente (`DEF-022-despues.txt`). |
| Análisis de impacto | Solo el generador del reporte predespliegue y su ejecución en CI. |
| Regresión ejecutada | Suite de pruebas del reporte y suite completa. |
| Estado | **Cerrado** |

### DEF-023 – Línea larga en la prueba de conteo de omitidas
| Campo | Valor |
|---|---|
| Detectado por | Ruff, regla E501, análisis estático del nuevo test |
| Severidad | Baja |
| Pasos para reproducir | Ejecutar `ruff check tests/componente/test_reporte_predespliegue.py`. |
| Resultado esperado / obtenido | Esperado: sin líneas fuera del límite. Obtenido: línea de 121 caracteres (`DEF-023-antes.txt`). |
| Causa encontrada (debugging) | La creación del XML de prueba y su codificación quedaron en una sola línea extensa. |
| Corrección | Se divide la llamada `write_text` en varias líneas; no se cambia el límite de Ruff. |
| Re-ejecución (confirmación) | Ruff check y format sobre el repositorio completo → sin hallazgos (`DEF-023-despues.txt`). |
| Análisis de impacto | Solo legibilidad de la prueba del reporte. |
| Regresión ejecutada | Suite completa de pytest. |
| Estado | **Cerrado** |

### DEF-024 – GitHub Actions no resuelve el tag de Trivy sin prefijo v
| Campo | Valor |
|---|---|
| Detectado por | GitHub Actions, preparación del job Trivy en CI |
| Severidad | Media (bloquea la compuerta de seguridad antes de escanear) |
| Pasos para reproducir | Ejecutar el workflow en `feature/ci` con `aquasecurity/trivy-action@0.36.0`. |
| Resultado esperado / obtenido | Esperado: inicia los escaneos. Obtenido: `Unable to resolve action ... unable to find version '0.36.0'` (`DEF-024-antes.txt`). |
| Causa encontrada (debugging) | El tag publicado por la acción incluye el prefijo `v`; el workflow usaba `0.36.0`. |
| Corrección | Se cambia la referencia en los tres pasos a `aquasecurity/trivy-action@v0.36.0`. |
| Re-ejecución (confirmación) | GitHub Actions `42105714319` resolvió la acción y generó los tres JSON de escaneo (`DEF-024-despues.txt`). |
| Análisis de impacto | Solo la ejecución de análisis Trivy en el CI. |
| Regresión ejecutada | El job pasó de error al preparar la acción a ejecutar fs/config/imagen. Los hallazgos de imagen quedan registrados en DEF-025. |
| Estado | **Cerrado** |

### DEF-025 – 46 vulnerabilidades HIGH en los paquetes del sistema de la imagen
| Campo | Valor |
|---|---|
| Detectado por | Trivy `image`, escaneo de seguridad del pipeline |
| Severidad | Alta |
| Pasos para reproducir | 1. Construir `testquiz:ci`. 2. Ejecutar Trivy imagen con severidades HIGH/CRITICAL. |
| Resultado esperado / obtenido | Esperado: 0 HIGH/CRITICAL. Obtenido: 46 HIGH, 0 CRITICAL en paquetes Debian de `python:3.12-slim`; fs y config sin bloqueos (`DEF-025-antes.txt`, CI). Confirmado en local con Trivy 0.76.1 el 2026-11-05: `Total: 46 (HIGH: 46, CRITICAL: 0)` (`DEF-025-antes-local.txt`); contando todas las severidades, 186 (46 HIGH, 72 MEDIUM, 62 LOW, 6 UNKNOWN). |
| Causa encontrada (debugging) | Diagnóstico con `trivy image --ignore-unfixed` sobre `testquiz:slim` (solo diagnóstico; el CI no usa esa opción): **0 de las 46 tenían versión corregida**. 45 tienen estado `affected` y 1 `fix_deferred` (CVE-2026-9538 en perl-base). Están en util-linux y sus bibliotecas, ncurses, systemd, acl, SQLite, perl-base y zlib de Debian 13 (`DEF-025-diagnostico-ignore-unfixed.txt`). Por eso **actualizar paquetes con apt no las resolvía**: Debian aún no publicó el parche. La salida real era cambiar de base. |
| Corrección | Mantenimiento **adaptativo**: commit `fix(docker): usa python:3.12-alpine como imagen base (DEF-025)` (`5370e31`). Se reemplaza la base Debian por Alpine 3.24 y el usuario sin privilegios se crea con `addgroup`/`adduser` de BusyBox (mismo uid/gid 10001, sin home y con `/sbin/nologin`). Las 46 vulnerabilidades **no se corrigieron**: se dejaron de usar los paquetes Debian que las tenían. No se cambió el umbral de Trivy ni se usó `--ignore-unfixed` en el CI. |
| Re-ejecución (confirmación) | `docker build -t testquiz:alpine .` y `trivy image --scanners vuln --severity HIGH,CRITICAL testquiz:alpine` → alpine 3.24.4: **0 hallazgos reportados**; sin filtro de severidad también 0. `trivy fs --scanners vuln,secret,misconfig` → 0; `trivy config` → 0 (`DEF-025-despues.txt`). Tamaño de la imagen: 259 MB → 151 MB. **Limitación:** según la documentación de Trivy v0.76.1 (`docs/guide/coverage/os/alpine.md`), para Alpine la detección de *unfixed vulnerabilities* no está soportada, porque los avisos de Alpine solo listan vulnerabilidades con parche. Para Debian sí lo está. Así que el 0 significa que **no hay hallazgos reportados**, no que el riesgo sea cero. Se mitiga repitiendo el escaneo en cada push del CI. |
| Análisis de impacto | Solo la imagen de despliegue (`Dockerfile`; Render usa `runtime: docker`). El código de la app no cambia. Riesgo revisado: Alpine usa musl en lugar de glibc; las dependencias (`pydantic-core`, `uvloop`, `httptools`, `watchfiles`) se instalaron desde ruedas musllinux sin compilar. El proceso sigue sin ser root (`id` → uid=10001). |
| Regresión ejecutada | Dentro del contenedor: `python -m pytest -q` → 277 passed, 2 skipped. Contenedor en marcha: `/salud` 200 con versión 1.0.0, healthcheck `healthy`, panel 403 sin token; con `empates_mal` el ejecutor del panel marcó Ranking y Partida CAIDO (4 fallidas) y tras reparar 0 fallidas (`DEF-026-despues.txt`). Local: `pytest -q` → 290 passed, 2 skipped. Confirmado en GitHub Actions: run 42161113908 (Trivy 0.70.0) y run 42170687291 (Trivy 0.76.1), imagen alpine 3.24.4 con 0 hallazgos. |
| Estado | **Cerrado** (0 hallazgos reportados en local, con la limitación anterior; el CI lo vuelve a comprobar en cada push) |

### DEF-026 – La suite no se ejecuta dentro de la imagen Docker (error de recolección)
| Campo | Valor |
|---|---|
| Detectado por | pytest dentro del contenedor (nivel sistema / despliegue), al validar la imagen con Docker local |
| Severidad | Alta (en el despliegue el panel del Saboteador no puede ejecutar las pruebas: el tablero de dominó queda inservible) |
| Pasos para reproducir | 1. `docker build -t testquiz:slim .` 2. `docker run --rm -e ADMIN_TOKEN=demo123 testquiz:slim python -m pytest -q -p no:cacheprovider` 3. Con el contenedor en marcha, activar `empates_mal` y llamar `POST /api/admin/pruebas`. |
| Resultado esperado / obtenido | Esperado: la suite corre y el panel marca Ranking y Partida como CAIDO. Obtenido: `ModuleNotFoundError: No module named 'scripts'` en `tests/componente/test_reporte_predespliegue.py`, `Interrupted: 1 error during collection`, **0 pruebas ejecutadas** (código 2). El panel devolvió `pruebas: 1, fallidas: 1, por_nivel: sin_nivel` y ningún módulo caído (`DEF-026-antes.txt`). |
| Causa encontrada (debugging) | `test_reporte_predespliegue.py` importa `scripts.reporte_predespliegue`, pero `.dockerignore` excluye `scripts/` (la imagen no lo necesita). Un solo error de recolección hace que pytest interrumpa toda la ejecución. La prueba pertenece al pipeline (evalúa el reporte predespliegue), no al servidor. |
| Corrección | Commit `fix(docker): excluye de la imagen la prueba del reporte predespliegue (DEF-026)` (`1ef6e54`): se agrega `tests/componente/test_reporte_predespliegue.py` a `.dockerignore`. La prueba se sigue ejecutando en el CI (job de pruebas), que sí tiene `scripts/`. No se borró ninguna prueba. |
| Re-ejecución (confirmación) | `docker run --rm -e ADMIN_TOKEN=demo123 testquiz:alpine python -m pytest -q -p no:cacheprovider` → **277 passed, 2 skipped**, código 0 (`DEF-026-despues.txt`). 277 = 290 de la suite − 13 pruebas del reporte predespliegue. |
| Análisis de impacto | Imagen Docker y panel del Saboteador en el despliegue (`app/calidad/ejecutor.py` lanza pytest dentro del servidor). La suite del CI no cambia: el job de pruebas sigue ejecutando las 13 pruebas del reporte. |
| Regresión ejecutada | Contenedor en marcha: panel con `empates_mal` → `pruebas: 279, fallidas: 4, caidos: Partida, Ranking, en_riesgo: API, Gestor`; tras `reparar` → 0 fallidas. Local: `pytest -q` → 290 passed, 2 skipped. |
| Estado | **Cerrado** |

### DEF-027 – Constante sin uso y engañosa en el script de carga
| Campo | Valor |
|---|---|
| Detectado por | Vulture 2.16 (análisis estático de código muerto), `performance/locustfile.py` |
| Severidad | Baja (mantenibilidad; no cambia el comportamiento) |
| Pasos para reproducir | 1. `vulture app scripts performance` 2. Buscar `MAX_JUGADORES` en el repositorio. |
| Resultado esperado / obtenido | Esperado: el script de carga no declara límites que no usa. Obtenido: `unused variable 'MAX_JUGADORES_POR_PARTIDA'` (`= 40`), mientras el límite real del juego es `MAX_JUGADORES_POR_DEFECTO = 50` en `app/dominio/partida.py` (`DEF-027-antes.txt`). |
| Causa encontrada (debugging) | La constante quedó de la primera versión del script: el reparto de jugadores se cambió en DEF-016 (elegir al azar entre partidas abiertas y buscar otra si responde 409 por partida llena) y nadie la volvió a leer. Quien la vea creería que el juego admite 40 jugadores por partida. |
| Corrección | Mantenimiento **perfectivo**: commit `fix(rendimiento): quita una constante sin uso del script de carga (DEF-027)` (`ec7b7e3`). Se borra la línea; el límite real sigue en `app/dominio/partida.py`. |
| Re-ejecución (confirmación) | `vulture app scripts performance` ya no muestra `MAX_JUGADORES_POR_PARTIDA` (`DEF-027-despues.txt`). |
| Análisis de impacto | Solo `performance/locustfile.py` (herramienta de prueba). La aplicación y los demás escenarios no lo usaban. |
| Regresión ejecutada | `pytest -q` → 296 passed, 3 skipped. Locust 20 usuarios / 30 s contra uvicorn local → 476 peticiones, 0 fallos, p95 10 ms (RNF-01 y RNF-02 cumplen). |
| Estado | **Cerrado** |

### DEF-028 – estado_publico usa la pregunta sin comprobar que exista (Sonar S2259)
| Campo | Valor |
|---|---|
| Detectado por | SonarQube Cloud, regla `pythonbugs:S2259` (bug, confiabilidad MEDIUM), primer análisis de la etapa 3 del CI (run 42257204499) |
| Severidad | Media |
| Pasos para reproducir | 1. Analizar la rama `feature/sonar` con SonarQube Cloud. 2. Ver `app/dominio/partida.py:346`. |
| Resultado esperado / obtenido | Esperado: no acceder a atributos de un valor que puede ser `None`. Obtenido: `estado["correcta"] = pregunta.correcta` en el estado RESULTADOS, aunque `pregunta` viene de `pregunta_actual`, que devuelve `None` si el índice queda fuera de rango (`DEF-028-antes.txt`). |
| Causa encontrada (debugging) | El bloque anterior sí comprueba `pregunta is not None`, pero el bloque de RESULTADOS no. Con el flujo normal el índice es válido en RESULTADOS, por eso ninguna prueba lo vio; si el estado y el índice se desalinean, `estado_publico` lanza `AttributeError` y la difusión por WebSocket se cae. |
| Corrección | Mantenimiento **correctivo**: commit `fix(partida): estado_publico solo revela la correcta si hay pregunta (DEF-028)` (`abfd30c`). Antes, la prueba `test_estado_publico_en_resultados_sin_pregunta_no_falla` se subió con `xfail(strict=True)` (`test(partida)`), y reproducía `AttributeError: 'NoneType' object has no attribute 'correcta'`. |
| Re-ejecución (confirmación) | La prueba pasa sin `xfail`; re-análisis de Sonar del commit `bce04eb` (run 42262436047): S2259 `CLOSED/FIXED` (`DEF-028-despues.txt`). |
| Análisis de impacto | `Partida.estado_publico`, que usan la API (`GET /api/partidas/{pin}`) y la difusión por WebSocket. Con el flujo normal el resultado no cambia: en RESULTADOS siempre hay pregunta. |
| Regresión ejecutada | `pytest -q` → 302 passed, 3 skipped; mutantes 6/6 en el CI; CI completo en verde. |
| Estado | **Cerrado** |

### DEF-029 – La cobertura de Sonar mezcla el front JS sin reporte con el backend
| Campo | Valor |
|---|---|
| Detectado por | SonarQube Cloud, condición `new_coverage` del Quality Gate (73,5 % < 80 %) |
| Severidad | Media (bloquea el Quality Gate) |
| Pasos para reproducir | 1. Correr la etapa 3 del CI. 2. Consultar `api/measures/component` de la rama y de `app/static/app.js`. |
| Resultado esperado / obtenido | Esperado: la cobertura de Sonar coincide con la de pytest-cov (97,55 %). Obtenido: 73,5 %; `app/static/app.js` aporta 307 líneas por cubrir con 0 % (`DEF-029-antes.txt`). |
| Causa encontrada (debugging) | Las rutas de `coverage.xml` sí se resolvieron: las 23 líneas sin cubrir de Python coinciden con pytest-cov. La diferencia (1247 − 940 = 307 líneas) es `app/static/app.js`: `sonar.sources=app` incluye el front de demostración, que no tiene herramienta de cobertura (no hay pruebas unitarias de JS; el front se prueba a nivel de sistema). |
| Corrección | Commit `fix(sonar): la cobertura mide el backend y no el front sin reporte (DEF-029)` (`aa4f184`): `sonar.coverage.exclusions=app/static/**`. Se excluye el front **solo de la métrica de cobertura**: Sonar lo sigue analizando (S9383 y S6850 salieron de esa carpeta). El umbral del 80 % no cambia. El front se prueba a nivel de sistema (`tests/sistema/test_front.py`). |
| Re-ejecución (confirmación) | re-análisis de Sonar del commit `bce04eb` (run 42262436047): `new_coverage` 97,6 % (OK, umbral < 80 sin cambios); 943 líneas por cubrir, 23 sin cubrir, las mismas que pytest-cov (`DEF-029-despues.txt`). |
| Análisis de impacto | Solo la configuración del análisis. No cambia código ni pruebas. |
| Regresión ejecutada | CI completo en verde, Quality Gate OK. |
| Estado | **Cerrado** |

### DEF-030 – Promesa sin manejar explícitamente en el front (Sonar S9383)
| Campo | Valor |
|---|---|
| Detectado por | SonarQube Cloud, regla `javascript:S9383` (bug, confiabilidad MEDIUM) |
| Severidad | Baja (la función ya captura sus errores por dentro) |
| Pasos para reproducir | Ver `app/static/app.js:207` en el análisis de `feature/sonar`. |
| Resultado esperado / obtenido | Esperado: toda promesa se espera, se captura o se marca como ignorada a propósito. Obtenido: `actualizarMarcador();` se llama sin `await`, sin `.catch` y sin `void` (`DEF-030-antes.txt`). |
| Causa encontrada (debugging) | `actualizarMarcador` es `async` y tiene su propio `try/catch`, así que hoy no deja promesas rechazadas; pero la llamada no lo dice y un cambio futuro dentro de la función sí podría dejar un rechazo sin manejar. |
| Corrección | Commit `fix(front): la actualizacion del marcador se marca como promesa ignorada a proposito (DEF-030)`: `void actualizarMarcador();` con un comentario que explica que la función captura sus errores. |
| Re-ejecución (confirmación) | `node --check app/static/app.js` OK; re-análisis de Sonar del commit `bce04eb` (run 42262436047): S9383 `CLOSED/FIXED` (`DEF-030-despues.txt`). |
| Análisis de impacto | Solo la vista del jugador en `app/static/app.js`. El comportamiento no cambia. |
| Regresión ejecutada | `pytest -q` (incluye `tests/sistema/test_front.py`) → 302 passed, 3 skipped. |
| Estado | **Cerrado** |

### DEF-031 – El log del panel registra la clave tal como llega en la URL (Sonar S5145)
| Campo | Valor |
|---|---|
| Detectado por | SonarQube Cloud, regla `pythonsecurity:S5145` (vulnerabilidad, seguridad LOW, análisis de flujo de datos) en `admin.activar()` y `admin.desactivar()` |
| Severidad | Baja |
| Pasos para reproducir | Ver `app/api/admin.py:83` y `:91` en el análisis de `feature/sonar`. |
| Resultado esperado / obtenido | Esperado: el log no escribe datos controlados por el cliente. Obtenido: `logger.warning("Sabotaje ACTIVADO: %s", clave)` con `clave` del path (`DEF-031-antes.txt`). |
| Causa encontrada (debugging) | Hoy no es explotable: `_validar_clave` responde 404 con cualquier clave fuera del catálogo antes de llegar al log, así que solo se registran las 6 claves conocidas. Pero el valor registrado sigue siendo el texto de la petición; si alguien quitara o cambiara la validación, se podrían inyectar saltos de línea en el log. |
| Corrección | Mantenimiento **preventivo**: commit `fix(api): el log del panel registra la clave del catalogo, no la de la URL (DEF-031)` (`b26b8d6`). `_validar_clave` devuelve `sabotaje.clave` del catálogo, y eso es lo que se activa y se registra. Pruebas de seguridad nuevas (`test(api)`): una clave con `%0A` responde 404 y no llega al log, y el log registra la clave del catálogo. Esas pruebas también pasaban antes porque la validación ya existía: son guardas de regresión, no la reproducción de un fallo. |
| Re-ejecución (confirmación) | re-análisis de Sonar del commit `bce04eb` (run 42262436047): los 2 S5145 `CLOSED/FIXED` (`DEF-031-despues.txt`). No hizo falta marcarlos a mano como falso positivo. |
| Análisis de impacto | `POST /api/admin/sabotajes/{clave}/activar` y `/desactivar`. Respuesta y efecto iguales; solo cambia de dónde sale el texto del log. |
| Regresión ejecutada | `pytest -q` → 302 passed, 3 skipped; mutantes 6/6 en el CI. |
| Estado | **Cerrado** |

### DEF-032 – Títulos vacíos en el HTML del front (Sonar S6850)
| Campo | Valor |
|---|---|
| Detectado por | SonarQube Cloud, regla `Web:S6850` (code smell, accesibilidad), 3 casos |
| Severidad | Baja |
| Pasos para reproducir | Ver `app/static/index.html:47, 53 y 83` en el análisis de `feature/sonar`. |
| Resultado esperado / obtenido | Esperado: todo título tiene contenido para lectores de pantalla. Obtenido: `<h3 id="prof-texto"></h3>`, `<h3 id="prof-ganador"></h3>` y `<h3 id="jug-texto"></h3>` vacíos (`DEF-032-antes.txt`). |
| Causa encontrada (debugging) | El JS rellena esos títulos cuando llega el estado de la partida; en el HTML inicial quedan vacíos. |
| Corrección | Commit `fix(front): los titulos del HTML tienen texto inicial (DEF-032)`: "Pregunta", "Resultados" y "Pregunta". El JS los reemplaza con `textContent` al llegar el estado, igual que antes. |
| Re-ejecución (confirmación) | re-análisis de Sonar del commit `bce04eb` (run 42262436047): los 3 S6850 `CLOSED/FIXED` (`DEF-032-despues.txt`). |
| Análisis de impacto | Solo `app/static/index.html`; los contenedores de esos títulos están ocultos hasta que el JS los rellena. |
| Regresión ejecutada | `pytest -q` → 302 passed, 3 skipped. |
| Estado | **Cerrado** |

### DEF-033 – Con dos sabotajes activos, el daño se atribuye al sabotaje equivocado
| Campo | Valor |
|---|---|
| Detectado por | pytest, nivel sistema: la prueba de contrato de la ventana de daño (`test_ventana_dano.py`) con `racha_no_suma` y `bono_sin_acierto` activos dio 3 respuestas afectadas para `bono_sin_acierto` en vez de 2. Reproducido a nivel de integración |
| Severidad | Media (el juego y los puntos son correctos, pero el panel y la ventana de daño mostrarían mal "daño por sabotaje" justo en la demo con dos sabotajes) |
| Pasos para reproducir | 1. Activar `racha_no_suma` y `bono_sin_acierto`. 2. Ana responde bien 2 preguntas en el límite y Beto responde mal y rápido. 3. Leer `resumen_por_sabotaje()` e `impacto_por_jugador()`. |
| Resultado esperado / obtenido | Esperado: `bono_sin_acierto` 2 respuestas / +950 y `racha_no_suma` 1 respuesta / −100. Obtenido: `bono_sin_acierto` 3 / +1050 y `racha_no_suma` 0 / 0; los −100 de Ana aparecen como +100 de `bono_sin_acierto` (`DEF-033-antes.txt`). La nota de la respuesta sí era correcta. |
| Causa encontrada (debugging) | En `Partida.responder`, cuando hay más de un sabotaje activo se recalcula la respuesta con cada sabotaje por separado (`solo_sabotajes([clave])`). Ese cálculo usa `jugador.racha_real`, pero esa racha ya se actualizó unas líneas antes con el acierto actual. Con la racha adelantada un paso, `bono_sin_acierto` "suma" 100 puntos de racha que no le tocan y `racha_no_suma` da diferencia 0. Con un solo sabotaje no pasa, porque ahí se usa la diferencia total. |
| Corrección | Mantenimiento **correctivo**: commit `fix(partida): el desglose por sabotaje usa la racha real previa (DEF-033)` (`d5de874`). Antes se subió la prueba con `xfail(strict=True)` (`769b4fe`). No cambia cómo se calculan los puntos mostrados ni los reales. |
| Re-ejecución (confirmación) | La prueba `test_desglose_con_dos_sabotajes_atribuye_cada_diferencia_a_su_sabotaje` pasa sin `xfail`; el escenario por HTTP da `bono_sin_acierto` 2 / +950 y `racha_no_suma` 1 / −100 (`DEF-033-despues.txt`). |
| Análisis de impacto | `Partida.responder` (solo la rama con más de un sabotaje activo), `impacto_por_jugador`, `resumen_por_sabotaje`, `GET /api/admin/partidas/{pin}/impacto`, el panel y la ventana de daño. |
| Regresión ejecutada | `pytest -q` → 320 passed, 3 skipped; `python scripts/verificar_mutantes.py` → 6/6. |
| Estado | **Cerrado** (la verificación en navegador encontró además DEF-034) |

### DEF-034 – Con dos sabotajes, el desglose por sabotaje no suma la diferencia total
| Campo | Valor |
|---|---|
| Detectado por | Verificación real en navegador (Playwright contra uvicorn, nivel sistema) de la ventana de daño, y reproducido con pytest a nivel de integración |
| Severidad | Media (puntos del juego correctos; el "daño por sabotaje" del panel y de la ventana queda corto en la demo con dos sabotajes) |
| Pasos para reproducir | 1. Activar `racha_no_suma` y `bono_sin_acierto`. 2. Un jugador acierta 3 preguntas seguidas. 3. Comparar `impacto_por_jugador()[...]["diferencia"]` con la suma de su `desglose`. |
| Resultado esperado / obtenido | Esperado: la suma del desglose de cada jugador es igual a su diferencia. Obtenido: Ana perdió −300 (−100 y −200), pero `racha_no_suma` suma −200 (`DEF-034-antes.txt`). |
| Causa encontrada (debugging) | Con más de un sabotaje, cada respuesta se recalcula con cada sabotaje por separado partiendo de la racha **real** anterior. Eso mide solo el efecto en esa respuesta, no el acumulado: con `racha_no_suma` la racha mostrada se quedó en 0 desde la pregunta 2, así que en la pregunta 3 el daño es −200, pero el cálculo aislado (racha real 2 → 2) da −100. DEF-033 corrigió que se usara la racha ya actualizada; esto es lo que faltaba. |
| Corrección | Mantenimiento **correctivo**: commit `fix(partida): el desglose por sabotaje acumula la racha de cada sabotaje (DEF-034)` (`2ea0ea1`), tras la prueba con `xfail(strict=True)` (`4dffac4`). La partida guarda por jugador una racha sombra por sabotaje activo: la que ese sabotaje habría dejado él solo; arranca en la racha real al activarse, se descarta al desactivarse y se reinicia cuando el jugador no responde (igual que la racha real). Puntos mostrados y reales sin cambios. |
| Re-ejecución (confirmación) | `test_desglose_con_dos_sabotajes_suma_la_diferencia_total` pasa; Playwright con la partida real: Ana −300 y desglose −300, Eva +422 = +422, Beto +1453 = +1453 (`DEF-034-despues.txt`). |
| Análisis de impacto | Igual que DEF-033. Costo: la complejidad ciclomática de `Partida.responder` sube de D (29) a E (33) (Radon); queda en la deuda técnica de `ANALISIS_ADICIONAL.md`. |
| Regresión ejecutada | `pytest -q` → 322 passed, 3 skipped; mutantes 6/6; las 6 pruebas de `test_impacto_sabotaje.py` en verde. |
| Estado | **Cerrado** |

### DEF-035 – La tabla de posiciones de la ventana de daño desborda en pantallas angostas
| Campo | Valor |
|---|---|
| Detectado por | Playwright (verificación real en navegador, nivel sistema, prueba de usabilidad) con pantalla de 390 px |
| Severidad | Baja (la ventana se proyecta en pantalla grande; en el celular aparece desplazamiento horizontal) |
| Pasos para reproducir | 1. Abrir `/dano.html` con una partida real en una pantalla de 390 px. 2. Comparar `scrollWidth` con el ancho visible. |
| Resultado esperado / obtenido | Esperado: la página no se desplaza a lo ancho. Obtenido: 413 px de documento en 390 px de pantalla; el elemento que se sale es la tabla `tabla-posiciones` (`DEF-035-antes.txt`). A 1600 y 1280 px no hay desborde. |
| Causa encontrada (debugging) | La tabla de respuestas está dentro de `.tabla-desplazable` (desplazamiento propio), pero la de posiciones no; con cinco columnas no cabe en 390 px menos los márgenes. |
| Corrección | Commit `fix(front): la tabla de posiciones se desplaza dentro de su panel en movil (DEF-035)` (`3b65147`): la tabla va dentro de `.tabla-desplazable`. Prueba de regresión `test_las_tablas_se_desplazan_dentro_de_su_panel`. |
| Re-ejecución (confirmación) | Playwright: 390 px de documento en 390 px de pantalla y ningún elemento fuera del borde; 1600 y 1280 px igual (`DEF-035-despues.txt`, `ventana-dano-movil.png`). |
| Análisis de impacto | Solo `app/static/dano.html`. |
| Regresión ejecutada | `pytest -q` → 322 passed, 3 skipped; `node --check app/static/dano.js`. |
| Estado | **Cerrado** |

### DEF-036 – El monitor de CPU se cuelga si Docker deja de responder
| Campo | Valor |
|---|---|
| Detectado por | Ejecución de la prueba de carga REST + WebSocket contra el contenedor (no funcional), revisando por qué el CSV de CPU tenía 2 muestras |
| Severidad | Baja (herramienta de prueba: se pierden los datos de CPU, no afecta a la aplicación) |
| Pasos para reproducir | 1. Lanzar `python performance\monitor_cpu.py salida.csv --contenedor <nombre>`. 2. Que el motor de Docker deje de responder durante la medición. |
| Resultado esperado / obtenido | Esperado: el monitor sigue escribiendo una fila cada 2 s (con CPU del servidor -1 si Docker no responde). Obtenido: 2 filas en 42 minutos (`DEF-036-antes.txt`). |
| Causa encontrada (debugging) | `_cpu_contenedor` llama a `subprocess.run(["docker", "stats", "--no-stream", ...])` sin `timeout`: si Docker no contesta, el monitor espera indefinidamente. |
| Corrección | Commit `fix(rendimiento): el monitor de CPU limita la espera de docker stats (DEF-036)` (`c50970c`): `timeout=10` en `subprocess.run`; si vence, la muestra registra -1 (sin dato) y el monitor sigue. Además, el orquestador de mediciones detiene cualquier corrida que supere el tiempo previsto y la marca inválida. |
| Re-ejecución (confirmación) | Prueba `test_cpu_del_contenedor_no_se_cuelga_si_docker_no_responde`: falla sin la corrección (`TimeoutExpired ... after None seconds`) y pasa con ella. Las 3 corridas reales contra el contenedor escribieron todas sus muestras (40, 103 y 99 filas) (`DEF-036-despues.txt`). |
| Análisis de impacto | Solo `performance/monitor_cpu.py` (herramienta de prueba). La aplicación no cambia. |
| Regresión ejecutada | `pytest -q` → 373 passed, 3 skipped; suite dentro del contenedor → 355 passed, 4 skipped. |
| Estado | **Cerrado** |

### DEF-037 – El monitor de CPU mide un proceso que no es Locust
| Campo | Valor |
|---|---|
| Detectado por | Ejecución de la prueba de carga REST + WebSocket contra Render (no funcional), al revisar la CPU del generador: 0,8 % con 50 usuarios |
| Severidad | Baja (herramienta de prueba: la columna de CPU del generador queda inválida; no afecta a la aplicación) |
| Pasos para reproducir | 1. Tener abierta una consola cuyo comando contenga "locust" (por ejemplo, la misma que va a lanzar Locust). 2. Lanzar `python performance\monitor_cpu.py salida.csv`. 3. Lanzar Locust. |
| Resultado esperado / obtenido | Esperado: el monitor mide el proceso de Locust. Obtenido: mide la consola (CPU máxima 0,8 %); `_procesos("locust")` devuelve una consola, un `python -c` y un `tail` que lee el log de Locust (`DEF-037-antes.txt`). |
| Causa encontrada (debugging) | `es_proceso` acepta el patrón en **cualquier parte** de cualquier argumento (`patron in arg`), y `main()` deja de buscar en cuanto encuentra un proceso. |
| Corrección | Commit `fix(rendimiento): el monitor de CPU solo reconoce el programa, no su nombre en un argumento (DEF-037)` (`0599294`): `es_proceso` compara el **nombre del programa** (`PureWindowsPath(arg).stem`) del ejecutable, del script que corre el intérprete o del módulo de `-m`, en vez de buscar el texto en cualquier argumento. |
| Re-ejecución (confirmación) | 6 pruebas nuevas en `test_monitor_cpu.py` fallan sin la corrección y pasan con ella; con una consola ficticia y un Locust real a la vez, el monitor solo encuentra `locust.exe` y sus `python.exe` (`DEF-037-despues.txt`). |
| Análisis de impacto | Solo `performance/monitor_cpu.py` (herramienta de prueba); la aplicación no cambia. Datos: la CPU del generador de `carga_ws_render` queda **sin dato**; la de `quiebre_render` es válida (sube con la carga, máx. 66 %, sin avisos de Locust); las del Paso 3 no se afectan (el orquestador no tenía "locust" en su comando). |
| Regresión ejecutada | `ruff check .`, `ruff format --check .`; `pytest -q` → 381 passed, 3 skipped. |
| Estado | **Cerrado** |
