# Bitácora de pruebas

Una fila por fase, agregada al terminarla. Las filas de las fases 0 a 5 se reconstruyeron el
2026-11-04 con `git log` y **volviendo a correr las pruebas** sobre el commit de cierre de cada fase
(`git worktree` en ese commit): los resultados y la cobertura son los reales de ese momento.

Cobertura = cobertura de líneas de `app/` con la suite completa en ese commit (`pytest --cov=app`).

| Fecha | Fase | Rama (commit de cierre) | Qué se probó (nivel y tipo) | Comando | Resultado | Cobertura | Hallazgos Ruff / SonarLint / Trivy | DEF |
|---|---|---|---|---|---|---|---|---|
| 2026-11-04 | 0 – Arranque | main (`0eb32e1`) | Sistema, funcional: `/salud` responde estado y versión. Estático: Ruff y pre-commit | `pytest -q tests/sistema/test_salud.py`; `pre-commit run --all-files` | 1 passed, 1 warning; Ruff y formato OK | 100 % | Ruff S101 en pruebas; aviso de obsolescencia de httpx en pytest; hook `ruff` heredado en pre-commit. SonarLint: extensión aún no instalada. Trivy: no aplica todavía | DEF-001, DEF-002, DEF-003 |
| 2026-11-04 | 1 – Plan de pruebas | feature/plan-pruebas (`144ec69`) | Solo documentación (plan, principios, ciclo de vida, defectos, métricas, buenas prácticas). Regresión de la suite existente | `pytest -q`; `ruff check .` | 1 passed, 1 warning; Ruff OK | 100 % | Ninguno | — |
| 2026-11-04 | 2 – Configuración | feature/configuracion (`5ad1326`) | Componente, funcional: valores por defecto, lectura del entorno y errores de `MAX_PARTIDAS`, `PARTIDA_TTL_MINUTOS` y `PERMITIR_SABOTAJE`. Sistema, no funcional (seguridad): cabeceras de seguridad, aviso sin ADMIN_TOKEN | `pytest -q tests/componente/test_config.py tests/sistema/test_seguridad.py` | 11 passed (suite: 12 passed, 1 warning) | 98 % | Ruff S105 en `test_config.py`; Ruff S105/S106 en `test_seguridad.py` | DEF-004, DEF-005 |
| 2026-11-04 | 3 – Modelos | feature/modelos (`72d39c3`) | Componente, funcional: validación de `Pregunta` (valores límite del índice 0 y 3, fuera de rango -1 y 4, opciones), carga por categoría, JSON mal formado, pregunta inválida | `pytest -q tests/componente/test_modelos.py tests/componente/test_preguntas.py` | 23 passed (suite: 35 passed, 1 warning) | 93 % | Ruff N818 en `ErrorPartida`; pytest detectó que el error de JSON mal formado no nombra el archivo | DEF-006, DEF-007 |
| 2026-11-04 | 4 – Puntaje v1 | feature/puntaje (`f74e890`) | Componente, funcional: valores límite de "a tiempo" (20,000 s cuenta; 20,001 s no), racha desde el 2.º acierto, tope 500, respuesta incorrecta o tarde = 0 | `pytest -q -m "componente and puntaje"` | 20 passed (suite: 55 passed, 1 warning) | 94 % | Ninguno | — |
