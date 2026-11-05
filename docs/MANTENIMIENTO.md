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
