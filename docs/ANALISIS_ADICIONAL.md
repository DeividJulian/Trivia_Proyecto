# Análisis estático adicional (Bloque 3)

Fecha: 2026-11-06. Rama `feature/ci`. Herramientas instaladas solo en el entorno local (no se agregan
al CI ni a `requirements`): Bandit 1.9.4, Radon 6.0.1, Vulture 2.16, pip-audit 2.10.1.
Alcance: `app/`, `scripts/` y `performance/` (las pruebas ya las revisa Ruff; el `assert` de las
pruebas es DEF-001).

| Herramienta | Qué revisa | Comando |
|---|---|---|
| Bandit | Patrones inseguros en Python | `bandit -r app scripts performance` |
| Radon | Complejidad ciclomática (CC) e índice de mantenibilidad (MI) | `radon cc -s -a app scripts performance`; `radon mi -s app scripts performance` |
| Vulture | Código muerto | `vulture app scripts performance` |
| pip-audit | Vulnerabilidades conocidas en las dependencias | `pip-audit -r requirements.txt` (y `-panel`, `-dev`) |

Salidas completas: [bandit.txt](evidencias/analisis/bandit.txt), [radon.txt](evidencias/analisis/radon.txt),
[vulture.txt](evidencias/analisis/vulture.txt), [pip-audit.txt](evidencias/analisis/pip-audit.txt).

## Tabla para la exposición

| Herramienta | Hallazgo | Decisión | Evidencia |
|---|---|---|---|
| Bandit | 15 avisos: 12 Low, 3 Medium, 0 High | **Ya tratados**: son las mismas reglas que Ruff revisa (S314, S603, S311) con `# noqa` justificado línea a línea, más los avisos B404/B405 de los `import` de esas mismas líneas. No se abre DEF | [bandit.txt](evidencias/analisis/bandit.txt); DEF-012, DEF-013, DEF-020 |
| Radon CC | Promedio **A (3,2)**. Cinco funciones sobre B: `Partida.responder` D (29), `armar_tablero` C (16), `leer_trivy` C (15), `leer_junit` C (12), `planificar_regresion` C (11) | **Deuda técnica documentada, sin refactor** (decisión del equipo a 3 días de la exposición: no arriesgar el demo). Están cubiertas por pruebas | [radon.txt](evidencias/analisis/radon.txt) |
| Radon MI | Todos los archivos en **A** | Sin acción | [radon.txt](evidencias/analisis/radon.txt) |
| Vulture | `MAX_JUGADORES_POR_PARTIDA = 40` sin uso en el script de carga, que además contradice el límite real (50) | **Hallazgo real → DEF-027**, corregido | [DEF-027-antes](evidencias/DEF-027-antes.txt) · [DEF-027-despues](evidencias/DEF-027-despues.txt) |
| Vulture | `data` en `conexiones.py` (100 % de confianza) | **Falso positivo** (ver abajo). No se cambia el código | [vulture.txt](evidencias/analisis/vulture.txt) |
| Vulture | 36 avisos de 60 %: rutas de FastAPI, campos de Pydantic y dataclasses, clases y atributos de Locust | **Falsos positivos**: el framework los usa por decorador o por introspección | [vulture.txt](evidencias/analisis/vulture.txt) |
| pip-audit | 0 vulnerabilidades conocidas en `requirements.txt`, `requirements-panel.txt` y `requirements-dev.txt` | Sin acción | [pip-audit.txt](evidencias/analisis/pip-audit.txt) |

## Bandit: a qué tratamiento corresponde cada aviso

| Aviso de Bandit | Dónde | Tratamiento existente |
|---|---|---|
| B314 (Medium) `ET.parse` | `app/calidad/ejecutor.py:54` | `# noqa: S314` — XML generado localmente por pytest (DEF-013) |
| B314 (Medium) ×2 | `scripts/reporte_predespliegue.py:34, 51` | `# noqa: S314` — XML generado dentro del pipeline (DEF-020) |
| B603 `subprocess` sin shell | `app/calidad/ejecutor.py:131` | `# noqa: S603` — pytest con argumentos propios; el panel no acepta argumentos libres (DEF-013) |
| B603 ×2 | `scripts/regresion_por_impacto.py:29, 60` | `# noqa: S603` (DEF-012) |
| B603 | `scripts/verificar_mutantes.py:33` | `# noqa: S603` (DEF-013) |
| B311 ×3 `random` | `performance/locustfile.py:48, 142, 146` | `# noqa: S311` — simulación de jugadores, no seguridad |
| B404 ×3 `import subprocess` | `ejecutor.py`, `regresion_por_impacto.py`, `verificar_mutantes.py` | Es el mismo riesgo que B603 en esos archivos: ya tratado arriba |
| B405 ×2 `import xml.etree` | `ejecutor.py`, `reporte_predespliegue.py` | Es el mismo riesgo que B314 en esos archivos: ya tratado arriba |

No se agregan comentarios `# nosec`: el riesgo ya está justificado en el `noqa` de Ruff de cada línea,
y duplicar la supresión solo añadiría ruido.

## Vulture: `data` en `conexiones.py`

```python
class Socket(Protocol):
    async def send_json(self, data: Any) -> None: ...
```

`Socket` es un `Protocol`: describe la forma que debe tener un WebSocket (el real de Starlette y el
doble de las pruebas). El cuerpo es `...`, así que el parámetro nunca se "usa", pero su nombre tiene
que coincidir con el de `starlette.websockets.WebSocket.send_json(data, mode="text")` para que ambos
cumplan el protocolo. Renombrarlo o borrarlo rompería ese contrato. **Falso positivo.**

## Deuda técnica de complejidad

CC: A 1–5, B 6–10, C 11–20, D 21–30. Ninguna función está en E o F.

| Función | CC | Por qué es compleja | Refactor propuesto (después de la exposición) | Pruebas que la cubren | Prioridad |
|---|---|---|---|---|---|
| `Partida.responder` (`app/dominio/partida.py`) | D (29) | Junta validaciones, puntos mostrados, evaluación sombra (puntos reales), desglose por sabotaje y la nota del daño | Extraer `_validar_respuesta`, `_evaluacion_sombra` y `_nota_de_impacto`; dejar `responder` como coordinadora | `tests/integracion/test_partida.py`, `test_impacto_sabotaje.py`, mutantes 6/6 | Media |
| `armar_tablero` (`app/calidad/ejecutor.py`) | C (16) | Tres recorridos (contar, marcar CAIDO, propagar EN_RIESGO) dentro de una función | Extraer `_contar_por_modulo` y `_propagar_riesgo` | `tests/componente/test_tablero.py` | Baja |
| `leer_trivy` (`scripts/reporte_predespliegue.py`) | C (15) | Lectura del JSON con dos errores posibles y tres bucles anidados por tipo de hallazgo | Extraer `_hallazgos_bloqueantes(datos)` | `tests/componente/test_reporte_predespliegue.py` | Baja |
| `leer_junit` (`app/calidad/ejecutor.py`) | C (12) | Comprensiones con condiciones y el caso `failure`/`error` | Extraer `_resultado_de_caso(caso)` | `tests/componente/test_tablero.py` | Baja |
| `planificar_regresion` (`app/calidad/impacto.py`) | C (11) | Clasifica cada archivo y elige entre cuatro motivos | Extraer `_clasificar_archivos` | `tests/componente/test_impacto.py` | Baja |

Por qué no se refactoriza ahora: `responder` y `armar_tablero` son justo el código que muestra el
demo del Saboteador (tablero de dominó y daño por jugador). Un refactor a tres días de la exposición
es un riesgo de regresión sin beneficio visible para el usuario. La complejidad queda medida,
explicada y con su plan: es **mantenimiento perfectivo planificado**.
