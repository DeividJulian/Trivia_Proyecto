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
