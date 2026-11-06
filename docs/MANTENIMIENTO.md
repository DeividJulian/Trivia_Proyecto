# Mantenimiento del software

## Tipos de mantenimiento en el proyecto

| Tipo | Qué es | Dónde aparece en TestQuiz |
|---|---|---|
| **Correctivo** | Corregir defectos encontrados | Todos los DEF cerrados de `REPORTE_DEFECTOS.md`: DEF-007 (JSON mal formado), DEF-008 a DEF-010 (validaciones halladas en las pruebas exploratorias), DEF-011 (bono a respuestas incorrectas) |
| **Adaptativo** | Adaptar el sistema a cambios del entorno | Actualizar dependencias o la imagen de Python cuando Trivy reporta vulnerabilidades (Fase 13); migrar del `httpx` del TestClient a `httpx2` (DEF-002); mantener los hooks de pre-commit al día (DEF-003) |
| **Perfectivo** | Mejorar rendimiento o mantenibilidad sin cambiar la funcionalidad | Mejoras tras el punto de quiebre (Fase 12): varios workers, estado en Redis; refactors que pida SonarQube (Fase 14) |
| **Evolutivo** | Agregar funcionalidades nuevas que pide el cliente | `SOLICITUD_CAMBIO_001.md`: bono por velocidad |
| **Preventivo** | Reducir el riesgo de fallos futuros | Pruebas nuevas que matan mutantes (Fase 11), pruebas que cubren los casos que dejaron pasar un defecto (p. ej. `test_respuesta_incorrecta_y_rapida_no_recibe_bono`) |

## El flujo de 5 pasos

Todo cambio, sea una corrección o una funcionalidad nueva, sigue el mismo flujo:

```
1. DETONANTE ──► 2. INTERVENCIÓN ──► 3. CONFIRMACIÓN ──► 4. ANÁLISIS DE IMPACTO ──► 5. REGRESIÓN
```

| Paso | Qué se hace | Ejemplo real: SOLICITUD_CAMBIO_001 + DEF-011 |
|---|---|---|
| 1. Detonante | Algo obliga a cambiar: un defecto, una vulnerabilidad, una petición del cliente | El profesor pide un bono por velocidad. Tag `v1-sin-bono` |
| 2. Intervención | Se modifica el código (con su prueba primero) | Pruebas nuevas del bono (xfail mientras no existía) y `calcular_bono_velocidad`. Tag `v2-cambio-con-error`: **GitHub Actions en rojo** |
| 3. Confirmación (re-ejecución) | Se vuelve a ejecutar **la prueba que falló** para confirmar que la corrección funciona | `fix(puntaje): el bono solo aplica a respuestas correctas (DEF-011)` y `pytest -v` de las 3 pruebas que fallaron → 3 passed |
| 4. Análisis de impacto | Se identifica qué otros módulos dependen de lo que cambió | Puntaje → Racha, Ranking, Partida, API (`SOLICITUD_CAMBIO_001.md`, `ANALISIS_IMPACTO.md`) |
| 5. Regresión | Se re-ejecutan las pruebas de los módulos afectados y luego la suite completa | `pytest -m "puntaje or ranking or partida or api"` → 127 passed; `pytest -q` → 178 passed. Tag `v3-corregido`: **GitHub Actions en verde** |

## Lecciones del efecto dominó

1. **Las pruebas nuevas pasaron y aun así había un error.** Solo probaban respuestas correctas.
   Las que lo detectaron fueron pruebas **que ya existían**: por eso la regresión es obligatoria.
2. **El error se propagó a tres niveles** (componente, sistema y aceptación) a partir de una sola
   línea. Cada nivel lo mostró de una forma distinta: 475 puntos, 1425 acumulados, un perdedor con
   puntos.
3. **Confirmación ≠ regresión.** Re-ejecutar la prueba que falló confirma la corrección; la
   regresión comprueba que la corrección no rompió otra cosa.
4. **La regresión no siempre es "probar todo".** Primero se hizo una regresión selectiva guiada
   por el análisis de impacto (127 de 178 pruebas) y luego la suite completa. El alcance depende
   del riesgo, del tamaño del cambio y del sistema.

## Tabla para la exposición: defectos y mantenimiento

Un renglón por defecto de `REPORTE_DEFECTOS.md`. "Riesgo aceptado" = la herramienta avisó, se revisó
y no era un defecto real: se documenta y se silencia **solo esa línea**, nunca la regla completa.

| DEF | Herramienta que lo detectó | Problema | Tipo de mantenimiento | Corrección | Verificación | Evidencia |
|---|---|---|---|---|---|---|
| DEF-001 | Ruff S101 | `assert` marcados como riesgo en las pruebas | Preventivo (riesgo aceptado) | Ignorar S101 solo en `tests/` | `ruff check .` limpio | [antes](evidencias/DEF-001-antes.txt) · [despues](evidencias/DEF-001-despues.txt) |
| DEF-002 | pytest (warnings) | Aviso de obsolescencia de `httpx` en el TestClient | Adaptativo (pendiente) | Migrar a `httpx2` cuando FastAPI lo soporte; no se oculta el aviso | El aviso sigue visible en cada ejecución | [antes](evidencias/DEF-002-antes.txt) |
| DEF-003 | pre-commit | Hook `ruff` heredado | Adaptativo | Hook `ruff-check` | `pre-commit run --all-files` | [antes](evidencias/DEF-003-antes.txt) · [despues](evidencias/DEF-003-despues.txt) |
| DEF-004 | Ruff S105 | Valor de prueba confundido con contraseña | Preventivo (riesgo aceptado) | `# noqa: S105` en una sola línea | `ruff check .` limpio | [antes](evidencias/DEF-004-antes.txt) · [despues](evidencias/DEF-004-despues.txt) |
| DEF-005 | Ruff S105/S106 | Tokens de prueba repetidos | Preventivo (riesgo aceptado) | Tokens centralizados en `tests/valores_prueba.py` | `ruff check .` limpio | [antes](evidencias/DEF-005-antes.txt) · [despues](evidencias/DEF-005-despues.txt) |
| DEF-006 | Ruff N818 | Nombre de la excepción base | Preventivo (riesgo aceptado) | `# noqa: N818` solo en `ErrorPartida` | `ruff check .` limpio | [antes](evidencias/DEF-006-antes.txt) · [despues](evidencias/DEF-006-despues.txt) |
| DEF-007 | pytest (componente) | JSON mal formado no dice qué archivo falló | Correctivo | El error indica archivo, línea y columna | Re-ejecución de la prueba + suite | [antes](evidencias/DEF-007-antes.txt) · [despues](evidencias/DEF-007-despues.txt) |
| DEF-008 | Prueba exploratoria | Nombre con solo espacios → 409 en vez de 422 | Correctivo | Validación del nombre en la API | Prueba de sistema nueva + suite | [antes](evidencias/DEF-008-antes.txt) · [despues](evidencias/DEF-008-despues.txt) |
| DEF-009 | Prueba exploratoria | `"opcion": true` contaba como opción 1 | Correctivo | La opción solo acepta enteros estrictos | Prueba de sistema nueva + suite | [antes](evidencias/DEF-009-antes.txt) · [despues](evidencias/DEF-009-despues.txt) |
| DEF-010 | Prueba exploratoria | PIN sin validar y errores que repiten la entrada | Correctivo | PIN de 6 dígitos (422) sin eco de la entrada | 2 confirmaciones (la 1.ª falló) + suite | [antes](evidencias/DEF-010-antes.txt) · [despues](evidencias/DEF-010-despues.txt) |
| DEF-011 | pytest (3 niveles) + GitHub Actions | Bono por velocidad en respuestas incorrectas (efecto dominó) | Correctivo | El bono solo aplica a respuestas correctas | 3 pruebas re-ejecutadas, regresión selectiva y completa; CI verde | [antes](evidencias/DEF-011-antes.txt) · [depuracion](evidencias/DEF-011-depuracion.txt) · [despues](evidencias/DEF-011-despues.txt) |
| DEF-012 | Ruff E402/S603 | Script de regresión por impacto | Preventivo (riesgo aceptado) | `# noqa` solo en 3 líneas, con motivo | `ruff check .` limpio | [antes](evidencias/DEF-012-antes.txt) · [despues](evidencias/DEF-012-despues.txt) |
| DEF-013 | Ruff S314/S603/E402 | Ejecutor de pruebas y verificar_mutantes | Preventivo (riesgo aceptado) | `# noqa` solo en esas líneas, con motivo | `ruff check .` limpio | [antes](evidencias/DEF-013-antes.txt) · [despues](evidencias/DEF-013-despues.txt) |
| DEF-014 | Locust (estrés) | Conexiones reiniciadas tras 5 s (keep-alive) | Correctivo | `--timeout-keep-alive 75` | Corrida de estrés de confirmación limpia | [antes](evidencias/DEF-014-antes.txt) · [despues](evidencias/DEF-014-despues.txt) |
| DEF-015 | Locust | El script avanzaba partidas no iniciadas (409 falsos) | Correctivo (herramienta de prueba) | El presentador no avanza si iniciar falló | Corrida de confirmación sin 409 | [antes](evidencias/DEF-015-antes.txt) · [despues](evidencias/DEF-015-despues.txt) |
| DEF-016 | Locust | El script agotaba el cupo de partidas: quiebre falso | Correctivo (herramienta de prueba) | Jugadores repartidos entre partidas abiertas | Corrida de confirmación limpia | [antes](evidencias/DEF-016-antes.txt) · [despues](evidencias/DEF-016-despues.txt) |
| DEF-017 | pytest (contenido de la imagen) | La imagen no podía correr la suite (faltaba `performance/`) | Correctivo | La imagen copia `performance/` | 254 passed con el contenido de la imagen | [antes](evidencias/DEF-017-antes.txt) · [despues](evidencias/DEF-017-despues.txt) |
| DEF-018 | Trivy rootfs | setuptools 70.3.0 dentro de pip (CVE-2025-47273) | Adaptativo / preventivo | La imagen final desinstala pip | `trivy fs` y `trivy config` en 0 | [antes](evidencias/DEF-018-antes.txt) · [despues](evidencias/DEF-018-despues.txt) |
| DEF-019 | SonarLint (VS Code) | Ternario anidado en el tablero (S3358) | Perfectivo | Función `describirModulo` | `node --check` + SonarLint sin aviso + suite | [antes](evidencias/DEF-019-antes.txt) · [despues](evidencias/DEF-019-despues.txt) |
| DEF-020 | Ruff S314 | Lectura del XML generado por el pipeline | Preventivo (riesgo aceptado) | `# noqa: S314` en 2 líneas | `ruff check .` limpio | [antes](evidencias/DEF-020-antes.txt) · [despues](evidencias/DEF-020-despues.txt) |
| DEF-021 | pytest (recolección) | f-string con barra invertida | Correctivo | Escapar antes de interpolar | 8 passed, 2 skipped | [antes](evidencias/DEF-021-antes.txt) · [despues](evidencias/DEF-021-despues.txt) |
| DEF-022 | Ejecución manual del CLI | El reporte no encontraba `performance` | Correctivo | Raíz del repo en `sys.path` | El CLI genera el reporte | [antes](evidencias/DEF-022-antes.txt) · [despues](evidencias/DEF-022-despues.txt) |
| DEF-023 | Ruff E501 | Línea larga en una prueba | Perfectivo | Dividir la línea; no se subió el límite | Ruff limpio | [antes](evidencias/DEF-023-antes.txt) · [despues](evidencias/DEF-023-despues.txt) |
| DEF-024 | GitHub Actions | Tag de Trivy sin prefijo `v` | Correctivo | `trivy-action@v0.36.0` | El job resolvió la acción y escaneó | [antes](evidencias/DEF-024-antes.txt) · [despues](evidencias/DEF-024-despues.txt) |
| DEF-025 | Trivy image | 46 HIGH en la base Debian de `python:3.12-slim` | Adaptativo | Base `python:3.12-alpine` (las 46 no tenían parche: se dejaron de usar esos paquetes, no se corrigieron) | Trivy image/fs/config: 0 hallazgos reportados (en Alpine Trivy no ve las que no tienen parche); 277 pruebas en el contenedor | [antes](evidencias/DEF-025-antes.txt) · [antes-local](evidencias/DEF-025-antes-local.txt) · [diagnóstico](evidencias/DEF-025-diagnostico-ignore-unfixed.txt) · [despues](evidencias/DEF-025-despues.txt) |
| DEF-026 | pytest dentro del contenedor | La suite no corría en la imagen; el panel quedaba inservible | Correctivo | Prueba del CI fuera de la imagen (`.dockerignore`) | 277 passed en el contenedor; panel marca CAIDO | [antes](evidencias/DEF-026-antes.txt) · [despues](evidencias/DEF-026-despues.txt) |
| DEF-027 | Vulture | Constante sin uso que contradecía el límite real de jugadores (40 vs. 50) | Perfectivo | Se borra la constante | Vulture sin el aviso; Locust 20 usuarios: 0 fallos | [antes](evidencias/DEF-027-antes.txt) · [despues](evidencias/DEF-027-despues.txt) |
| DEF-028 | SonarQube Cloud (S2259) | `estado_publico` usaba la pregunta sin comprobar que existiera | Correctivo | Revelar la correcta solo si hay pregunta; prueba primero con `xfail` estricto | La prueba reprodujo el `AttributeError` y luego pasó; Sonar: FIXED | [antes](evidencias/DEF-028-antes.txt) · [despues](evidencias/DEF-028-despues.txt) |
| DEF-029 | SonarQube Cloud (Quality Gate) | Cobertura 73,5 %: contaba el front JS sin reporte | Adaptativo | Excluir `app/static/**` solo de la cobertura; umbral del 80 % sin cambios | Cobertura 97,6 %, igual que pytest-cov | [antes](evidencias/DEF-029-antes.txt) · [despues](evidencias/DEF-029-despues.txt) |
| DEF-030 | SonarQube Cloud (S9383) | Promesa sin manejar explícitamente en el front | Preventivo | `void actualizarMarcador()` | `node --check`; Sonar: FIXED | [antes](evidencias/DEF-030-antes.txt) · [despues](evidencias/DEF-030-despues.txt) |
| DEF-031 | SonarQube Cloud (S5145) | El log registraba la clave tal como llegaba en la URL | Preventivo | Registrar la clave del catálogo; pruebas de seguridad | Sonar: FIXED (2 casos) | [antes](evidencias/DEF-031-antes.txt) · [despues](evidencias/DEF-031-despues.txt) |
| DEF-032 | SonarQube Cloud (S6850) | Títulos vacíos en el HTML (accesibilidad) | Perfectivo | Texto inicial en los 3 títulos | Sonar: FIXED (3 casos) | [antes](evidencias/DEF-032-antes.txt) · [despues](evidencias/DEF-032-despues.txt) |

## Mantenimiento preventivo sin defecto previo (Bloque 2)

No los detectó una prueba: se hicieron para que un fallo futuro no llegue al despliegue.

| Cambio | Riesgo que evita | Tipo | Verificación |
|---|---|---|---|
| Acciones de GitHub fijadas por SHA (`trivy-action@ed142fd… # v0.36.0` y las de `actions/*`) | Una etiqueta se puede mover. El 19-03-2026 un atacante reescribió 76 de las 77 etiquetas de `aquasecurity/trivy-action` con malware que roba credenciales (aviso GHSA-69fq-xp46-6x23). Con el SHA se ejecuta siempre el mismo código revisado | Preventivo | Antes de fijarlas se comprobó que `@v4`/`@v5` apuntaban al mismo SHA (sin cambio de comportamiento); CI run 42168456389 en verde |
| Imagen base fijada por digest (`python:3.12-alpine@sha256:213242b5…`) | Que la misma versión del código produzca imágenes distintas sin que nadie lo note | Preventivo | Build, Trivy (0 hallazgos) y 277 pruebas dentro del contenedor con el digest |
| `.github/dependabot.yml` (docker y github-actions, contra `develop`) | Que fijar versiones congele también las vulnerabilidades. Dependabot propone el digest o SHA nuevo y el PR pasa por todo el pipeline, Trivy incluido | Adaptativo / preventivo | Solo actúa cuando el archivo llegue a `main` (rama por defecto) |
| `/salud` informa `commit` y el humo espera ese SHA | Que el humo pase contra la versión **anterior** mientras Render aún despliega (VERSION siempre vale 1.0.0) | Preventivo | Humo contra el contenedor: con el commit correcto 3 passed; con otro commit falla `test_responde_el_commit_recien_desplegado` |
| El release se crea después del humo | Publicar un release de una versión que no arrancó bien | Preventivo | Orden de los jobs: 7 despliega, 8 corre el humo y luego crea el release |

## SonarQube Cloud: antes y después (rama `feature/sonar`)

| Métrica | Primer análisis (`f0f1ed1`) | Re-análisis (`bce04eb`) |
|---|---|---|
| Quality Gate | **ERROR** (confiabilidad, seguridad y cobertura) | **OK** |
| Bugs | 2 | 0 |
| Vulnerabilidades | 2 | 0 |
| Code smells | 3 | 0 |
| Security hotspots | 0 | 0 |
| Duplicación | 0,0 % | 0,0 % |
| Cobertura | 73,5 % | 97,6 % |

Las 7 incidencias las cerró Sonar como **FIXED** al volver a analizar; ninguna se marcó a mano como
falso positivo. Evidencias: [primer análisis](evidencias/SONAR-primer-analisis.txt) ·
[re-análisis](evidencias/SONAR-segundo-analisis.txt).

Por qué fallaba en "New Code": `main` sigue en la fase 0, así que para la rama todo el código es
código nuevo. La solución no fue tocar el umbral, sino corregir las incidencias.
