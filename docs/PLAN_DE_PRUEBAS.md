# Plan de pruebas – TestQuiz El Saboteador

## 1. Objetivo de prueba

> **Obtener evidencia de que el puntaje y el ranking son correctos en los escenarios críticos
> (respuesta en el límite de tiempo, rachas, empates) y conocer los riesgos que quedan antes de
> desplegar.**

El objetivo es medible (escenarios críticos definidos), está ligado a un riesgo de negocio (un
ranking injusto arruina la partida en vivo) y apoya una decisión: **desplegar o no desplegar**.

## 2. Alcance

| Dentro del alcance | Fuera del alcance |
|---|---|
| Reglas de puntaje, racha y ranking | Interfaz gráfica (front) |
| Máquina de estados de la partida | Persistencia en base de datos (todo está en memoria) |
| API REST, WebSocket y panel de administrador | Navegadores y dispositivos móviles |
| Rendimiento (carga y punto de quiebre) | Pruebas de usabilidad |
| Seguridad (análisis estático, Trivy, token admin) | Pruebas de penetración externas |

## 3. Características de calidad ISO/IEC 25010 priorizadas

| Prioridad | Característica | Pregunta de testing | Tipo de prueba | Métrica | Decisión que apoya |
|---|---|---|---|---|---|
| 1 | Adecuación funcional | ¿El puntaje y el ranking se calculan según las reglas? | Funcional (componente, integración, sistema, aceptación) | % de pruebas aprobadas; % de mutantes detectados | Si falla una prueba o sobrevive un mutante, **no se despliega** |
| 2 | Eficiencia de desempeño | ¿Responde rápido con una clase completa jugando? | No funcional: carga y estrés (Locust) | p95 en ms y % de fallos | Si p95 ≥ 500 ms con 50 usuarios se registra un defecto no funcional y se prioriza la mejora |
| 3 | Seguridad | ¿Puede alguien sin token sabotear la partida o el servidor? | Seguridad: pruebas del panel admin, Ruff (S), Sonar, Trivy | Nº de vulnerabilidades HIGH/CRITICAL; respuestas 403 correctas | Con una HIGH/CRITICAL abierta **no se despliega** |
| 4 | Fiabilidad | ¿El juego sigue si un jugador se desconecta o responde dos veces? | Funcional negativo y de robustez (WebSocket cerrado, doble respuesta) | % de respuestas 5xx; pruebas de robustez aprobadas | Un 5xx en las pruebas bloquea el despliegue |
| 5 | Mantenibilidad | ¿Podemos cambiar una regla sin romper otras sin enterarnos? | Estático (Ruff, Sonar) y regresión por análisis de impacto | Cobertura; Quality Gate; deuda técnica | Cobertura < 85 % o Quality Gate en rojo bloquean el despliegue |

## 4. Niveles ISTQB y carpeta que los cubre

| Nivel | Carpeta | Qué cubre | Marcador pytest |
|---|---|---|---|
| Componente | `tests/componente/` | Funciones aisladas: puntaje, racha, ranking, preguntas, configuración | `componente` |
| Integración de componentes | `tests/integracion/` | Partida + puntaje + ranking; gestor de partidas | `integracion` |
| Sistema | `tests/sistema/` | La aplicación completa por HTTP y WebSocket (TestClient) | `sistema` |
| Integración de sistemas | `tests/integracion_sistemas/` | Prueba de humo contra el servidor desplegado en Render | `integracion_sistemas` |
| Aceptación | `tests/aceptacion/` | Historias de usuario (Dado / Cuando / Entonces) usando solo la API pública | `aceptacion` |

## 5. Matriz NIVEL × TIPO

| Nivel | Funcional | No funcional |
|---|---|---|
| Componente | `test_puntaje.py::test_respuesta_justo_en_el_limite_cuenta_a_tiempo`, `test_ranking.py::test_empate_en_puntos_gana_el_de_menor_tiempo` | — |
| Integración | `test_partida.py::test_flujo_lobby_pregunta_resultados_finalizada`, `test_partida.py::test_puntaje_racha_y_ranking_juntos` | — |
| Sistema | `test_api.py::test_partida_completa_de_extremo_a_extremo`, `test_api.py::test_partida_inexistente_responde_404` | `test_no_funcional.py::test_responder_tarda_menos_de_medio_segundo`, `test_no_funcional.py::test_estado_con_100_jugadores_es_rapido`, `test_seguridad.py::test_respuestas_incluyen_cabeceras_de_seguridad` |
| Integración de sistemas | `test_humo.py::test_flujo_basico_en_servidor_desplegado` | `test_humo.py::test_panel_admin_desplegado_exige_token` (seguridad) |
| Aceptación | `test_historias.py::test_hu01_profesor_crea_partida_y_tres_estudiantes_juegan` | Locust: `performance/locustfile.py` (carga) y `performance/punto_quiebre.py` (estrés) |

## 6. Requisitos no funcionales

| ID | Requisito | Herramienta | Umbral |
|---|---|---|---|
| RNF-01 | Tiempo de respuesta con 50 usuarios concurrentes | Locust + `verificar_umbrales.py` | p95 < 500 ms |
| RNF-02 | Tasa de fallos con 50 usuarios | Locust + `verificar_umbrales.py` | < 1 % |
| RNF-03 | Responder una pregunta | `test_no_funcional.py` | < 0,5 s |
| RNF-04 | Vulnerabilidades | Trivy (fs, config e imagen) | 0 HIGH/CRITICAL |
| RNF-05 | Calidad del código | SonarQube Cloud | Quality Gate aprobado |
| RNF-06 | Cobertura de pruebas | pytest-cov | ≥ 85 % |
| RNF-07 | Efectividad de las pruebas | `verificar_mutantes.py` | 100 % de mutantes detectados |

**Punto de quiebre:** el escalón de usuarios en el que los fallos superan el **5 %** o el p95
supera **2000 ms**.

## 7. Criterios de entrada

- El código pasa `ruff check` y `ruff format --check` (pre-commit).
- Las historias de usuario tienen criterios de aceptación escritos.
- El entorno local arranca con `uvicorn app.main:app` y `/salud` responde.

## 8. Criterios de salida (antes de desplegar)

Se despliega **solo** si se cumplen todos:

1. 100 % de las pruebas de componente, integración, sistema y aceptación aprobadas.
2. Cobertura ≥ 85 % (RNF-06).
3. 6/6 mutantes del Saboteador detectados (RNF-07).
4. Quality Gate de Sonar aprobado (RNF-05).
5. 0 vulnerabilidades HIGH/CRITICAL en Trivy (RNF-04).
6. RNF-01 y RNF-02 cumplidos en la prueba de carga.
7. Ningún defecto de severidad Alta o Crítica abierto en `REPORTE_DEFECTOS.md`.

El veredicto lo calcula `scripts/reporte_predespliegue.py`: **APTO PARA DESPLEGAR** o **NO DESPLEGAR**.
