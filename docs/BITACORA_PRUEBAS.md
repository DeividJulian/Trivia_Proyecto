# Bitácora de pruebas

Una fila por fase, agregada al terminarla. Las filas de las fases 0 a 5 se reconstruyeron el
2026-11-04 con `git log` y **volviendo a correr las pruebas** sobre el commit de cierre de cada fase
(`git worktree` en ese commit): los resultados y la cobertura son los reales de ese momento.

Cobertura = cobertura de líneas de `app/` con la suite completa en ese commit (`pytest --cov=app`).

| Fecha | Fase | Rama (commit de cierre) | Qué se probó (nivel y tipo) | Comando | Resultado | Cobertura | Hallazgos Ruff / SonarLint / Trivy | DEF |
|---|---|---|---|---|---|---|---|---|
| 2026-11-04 | 0 – Arranque | main (`0eb32e1`) | Sistema, funcional: `/salud` responde estado y versión. Estático: Ruff y pre-commit | `pytest -q tests/sistema/test_salud.py`; `pre-commit run --all-files` | 1 passed, 1 warning; Ruff y formato OK | 100 % | Ruff S101 en pruebas; aviso de obsolescencia de httpx en pytest; hook `ruff` heredado en pre-commit. SonarLint: extensión aún no instalada. Trivy: no aplica todavía | DEF-001, DEF-002, DEF-003 |
| 2026-11-04 | 1 – Plan de pruebas | feature/plan-pruebas (`144ec69`) | Solo documentación (plan, principios, ciclo de vida, defectos, métricas, buenas prácticas). Regresión de la suite existente | `pytest -q`; `ruff check .` | 1 passed, 1 warning; Ruff OK | 100 % | Ninguno | — |
