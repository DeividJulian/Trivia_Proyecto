# Prompt para continuar el proyecto (equipo)

> Copia TODO el bloque de abajo y pégalo como primer mensaje a tu asistente de IA (Claude Code u
> otro) en VS Code, **con la carpeta del repositorio ya clonada y abierta**.

---

```text
Eres un ingeniero backend/QA que continúa el proyecto "TestQuiz – El Saboteador" (trivia en vivo
tipo Kahoot con un modo Saboteador de mutantes controlados). Proyecto final de Pruebas y
Mantenimiento de Software (UCC Pasto). Exposición: 9 de noviembre de 2026.
Trabajo en Windows (CMD) con VS Code. Acabo de clonar el repositorio:
https://github.com/DeividJulian/Trivia_Proyecto.git

=============================== ANTES DE TOCAR NADA ===============================
1. Lee COMPLETO el archivo CLAUDE.md de la raíz: tiene las 12 reglas del proyecto y el estado
   actual. Esas reglas son obligatorias (commits pequeños, pruebas tras cada función, ciclo de
   defectos DEF-00X, evidencias, bitácora, nunca subir secretos, etc.).
2. Lee también: docs/PLAN_DE_PRUEBAS.md, docs/REPORTE_DEFECTOS.md (DEF-001 a DEF-018),
   docs/BITACORA_PRUEBAS.md y docs/ANALISIS_IMPACTO.md.
3. Todo el trabajo está en la rama develop (main solo tiene el arranque hasta el cierre):
     git checkout develop
     git pull
4. Prepara el entorno (Python 3.12 recomendado; también funciona con 3.13/3.14):
     python -m venv .venv
     .venv\Scripts\activate
     pip install -r requirements-dev.txt
     pre-commit install
     pytest -q                              (deben pasar 259 pruebas)
     python scripts\verificar_mutantes.py   (deben salir 6/6 DETECTADO)
5. Para ver la app:
     set ADMIN_TOKEN=demo123
     uvicorn app.main:app --port 8000 --timeout-keep-alive 75
   Front de demo: http://127.0.0.1:8000/  ·  API: http://127.0.0.1:8000/docs
   Usa 127.0.0.1 y no localhost (en Windows localhost agrega ~2 s por conexión, ver DEF-014).

============================== CÓMO TRABAJAMOS EN EQUIPO ==============================
- Somos 3. Cada tarea en su propia rama: git checkout -b feature/<nombre> desde develop
  actualizado. Al terminar: pytest -q, ruff check ., ruff format --check ., y luego
  git checkout develop && git pull && git merge --no-ff feature/<nombre> -m "merge: ..." && git push.
  Si hay conflictos, resuélvelos y vuelve a correr pytest antes del push.
- Un commit = un cambio lógico; Conventional Commits en español; git push después de cada commit.
- NUMERACIÓN DE DEFECTOS (para no chocar): antes de crear un DEF, haz git pull de develop y usa
  el siguiente número libre en docs/REPORTE_DEFECTOS.md. Si dos personas crean a la vez, el que
  haga merge después renumera el suyo.
- Al terminar cada tarea agrega una fila en docs/BITACORA_PRUEBAS.md con datos REALES (comando,
  resultado, cobertura, hallazgos) y actualiza la sección "Estado actual" de CLAUDE.md.
- Si una herramienta (pytest, Ruff, Trivy, Sonar) detecta algo: DEF + evidencias
  docs/evidencias/DEF-00X-antes.txt y -despues.txt + commit "fix(...): ... (DEF-00X)" +
  re-ejecución + regresión. Si lo detecta SonarQube for IDE (SonarLint) en VS Code: DETENTE y
  pide al humano una captura antes (DEF-00X-antes.png) y otra después (DEF-00X-despues.png).
- Si necesitas que el humano haga algo (web, secreto, instalar algo), DETENTE y explícale paso a paso.
- NO cambies umbrales ni borres pruebas para que algo pase. NO subas secretos.

===================== LO QUE YA ESTÁ HECHO (no lo rehagas) =====================
- Fases 0 a 13: configuración, modelos, puntaje con bono por velocidad, ranking, partida, gestor,
  API REST + WebSocket, aceptación (5 historias), exploratorias, efecto dominó (tags v1-sin-bono,
  v2-cambio-con-error, v3-corregido), análisis de impacto, Saboteador (6 mutantes, panel admin,
  tablero de dominó, verificar_mutantes 6/6), rendimiento con Locust (carga y punto de quiebre
  local), Dockerfile y Trivy (fs y config limpios).
- Front de demostración en app/static (profesor, jugador y panel del Saboteador).
- CI mínimo en .github/workflows/ci.yml (Ruff + pytest).

=========================== LO QUE FALTA (en este orden) ===========================

---------------------------------------------------------------------------------
TAREA 1 – DEF-019: hallazgo de SonarQube for IDE en app/static/app.js (rama feature/def-019)
---------------------------------------------------------------------------------
SonarLint marcó javascript:S3358 ("Extract this nested ternary operation into an independent
statement") en app/static/app.js, en el texto de cada módulo del tablero de dominó
(detalle.textContent = ... ? ... : ... ? ... : ...).
- Pide al humano la captura ANTES (docs/evidencias/DEF-019-antes.png).
- Regístralo como DEF-019 en docs/REPORTE_DEFECTOS.md (detectado por SonarLint, severidad Baja,
  code smell de mantenibilidad).
- Corrige con un if/else o una función describirModulo(datos) en su propio commit:
  "fix(front): reemplaza el ternario anidado del tablero (DEF-019)".
- Verifica con node --check app\static\app.js y pytest -q; pide la captura DESPUÉS.

---------------------------------------------------------------------------------
TAREA 2 – NUEVA FUNCIONALIDAD: "Impacto del sabotaje" en el panel de administrador
           (rama feature/impacto-sabotaje)
---------------------------------------------------------------------------------
OBJETIVO: cuando el administrador activa sabotajes y la partida sigue, el panel debe mostrar, al
lado de cada sabotaje y por jugador, CUÁNTOS PUNTOS le cambió el sabotaje y CUÁLES son los puntos
REALES que debería tener. Ejemplo: con "racha_no_suma" activo, si Ana acierta 3 seguidas, el
panel debe mostrar "Ana: 3 450 mostrados · 3 750 reales · −300 por racha_no_suma".

IDEA DE DISEÑO (puntaje "sombra"): cada vez que alguien responde, se calcula dos veces el
resultado: el que se ve (con los sabotajes activos) y el real (como si no hubiera sabotajes).
El código del juego NO se modifica en caliente: se agrega una forma de evaluar sin mutantes.

Pasos (un commit por paso, cada función seguida de sus pruebas):

A) app/dominio/sabotajes.py
   - Context manager sin_sabotajes() basado en contextvars.ContextVar: dentro del bloque,
     esta_activo() devuelve False para todo, SIN tocar la lista global de activos (otros
     jugadores/peticiones no deben verse afectados).
   - (Opcional, para atribuir) solo_sabotajes(claves): dentro del bloque solo cuentan esas claves.
   - Pruebas de componente: dentro de sin_sabotajes() todo está inactivo y al salir se restaura;
     anidado y con excepciones también se restaura.

B) app/dominio/modelos.py – Jugador: agregar puntos_reales, racha_real y tiempo_total_real
   (por defecto 0). Nuevo dataclass ImpactoRespuesta: numero_pregunta, jugador, opcion,
   correcta (bool), sabotajes_activos (tuple), puntos_mostrados, puntos_reales, diferencia
   (= mostrados − reales), racha_mostrada, racha_real, segundos_extra, nota (texto corto).

C) app/dominio/partida.py
   - responder(nombre, opcion, tiempo_recibido: float | None = None): además de lo actual, calcula
     el resultado real con sabotajes.sin_sabotajes() usando jugador.racha_real y el tiempo real
     (tiempo_recibido si viene; si no, el mismo tiempo). Acumula puntos_reales, racha_real y
     tiempo_total_real, y agrega un ImpactoRespuesta a self.impacto (lista).
   - no_guarda_respuesta: si el jugador YA había respondido esa pregunta (se detecta con un
     registro paralelo que NO depende del mutante), la respuesta real vale 0 (no debió aceptarse)
     y nota = "respuesta repetida: sin el sabotaje habría sido rechazada (409)".
   - ranking_real(): ranking con puntos_reales, tiempo_total_real y SIN sabotajes (para
     empates_mal se compara posición mostrada vs posición real).
   - impacto_por_jugador(): por jugador → puntos_mostrados, puntos_reales, diferencia,
     posicion_mostrada, posicion_real, racha_mostrada, racha_real, y desglose
     {clave_sabotaje: diferencia_atribuida}. Atribución: si en la respuesta había un solo
     sabotaje activo, toda la diferencia es suya; si había varios, recalcula con
     solo_sabotajes([clave]) para cada uno (o reparte como "combinado" si no implementas el opcional).
   - IMPORTANTE: el comportamiento visible del juego NO cambia. Después de este paso
     python scripts\verificar_mutantes.py debe seguir dando 6/6 y pytest -q todo en verde.

D) app/api/rutas.py – en POST /respuestas mide partida.tiempo_transcurrido() AL LLEGAR la
   petición (antes del retardo del mutante respuesta_lenta) y pásalo como tiempo_recibido. Así el
   panel puede mostrar "+1,5 s y −37 puntos de bono por respuesta_lenta".

E) app/api/admin.py (protegido con X-Admin-Token como el resto del panel):
   - GET /api/admin/partidas → lista de partidas activas: pin, estado, jugadores, pregunta actual.
   - GET /api/admin/partidas/{pin}/impacto → { sabotajes_activos, jugadores: [...impacto por
     jugador...], respuestas: [...ImpactoRespuesta...], resumen_por_sabotaje: { clave:
     { respuestas_afectadas, puntos_de_diferencia } } }.
   - 403 sin token, 404 si el PIN no existe o PERMITIR_SABOTAJE=false (igual que el panel actual).

F) app/static (front, en la pestaña Saboteador): nueva tarjeta "Impacto en la partida":
   - Selector de partida (se llena con GET /api/admin/partidas) y refresco automático cada 2 s.
   - Tabla por jugador: Jugador | Puntos mostrados | Puntos reales | Diferencia | Posición
     mostrada → real | Racha mostrada / real. Diferencia en rojo si el sabotaje le QUITÓ puntos
     (ej. racha_no_suma, respuesta_lenta) y en naranja si le DIO puntos de más (ej.
     bono_sin_acierto, no_guarda_respuesta). Posición resaltada si cambió (empates_mal).
   - Al lado de cada sabotaje activo en la lista, un resumen: "afectó 4 respuestas · −300 pts".
   - Lista de las últimas respuestas afectadas con su nota (ej. "Pregunta 3 · Beto respondió MAL
     en 1,0 s · recibió +475 que no le correspondían (bono_sin_acierto)").
   - Sin dependencias externas; textos visibles en español; node --check app\static\app.js.

G) Pruebas (marca nivel y módulo con pytest.mark como el resto):
   - integración: con racha_no_suma, 3 aciertos justo en el límite → reales 1000+1100+1200=3300,
     mostrados 3000, diferencia −300.
   - integración: con bono_sin_acierto, respuesta incorrecta a 1 s de 20 → mostrados 475,
     reales 0, diferencia +475.
   - integración: con empates_mal y dos jugadores empatados en puntos → posición mostrada distinta
     de la real.
   - integración: con no_guarda_respuesta, responder dos veces → la 2.ª tiene reales 0 y nota.
   - integración: con tiempo_estricto, respuesta justo en el límite → mostrados 0, reales 1000.
   - sistema: con respuesta_lenta (retardo reducido con monkeypatch como en
     tests/sistema/test_no_funcional.py) → segundos_extra ≈ retardo y diferencia negativa.
   - sistema/seguridad: /api/admin/partidas y /impacto responden 403 sin token.
   - sistema: sin sabotajes, mostrados == reales para todos (diferencia 0).
   - Corre python scripts\verificar_mutantes.py: debe seguir en 6/6.
   - Actualiza docs (README: cómo usar la vista; BITACORA_PRUEBAS.md; CLAUDE.md).

---------------------------------------------------------------------------------
TAREA 3 – FASE 14: SonarQube Cloud (rama feature/sonar)
---------------------------------------------------------------------------------
DETENTE y guía al humano para:
  1. Entrar a sonarcloud.io con GitHub e importar el repo Trivia_Proyecto.
  2. Desactivar "Automatic Analysis" (Administration → Analysis Method).
  3. Generar un token y guardarlo en GitHub como secreto SONAR_TOKEN (no imprimirlo).
  4. Darte la organization y la projectKey.
Commits:
  chore(sonar): sonar-project.properties (projectKey, organization, sonar.sources=app,
    sonar.tests=tests, sonar.python.version=3.12, sonar.python.coverage.reportPaths=coverage.xml,
    sonar.qualitygate.wait=true)
Cada hallazgo de Sonar (bugs, vulnerabilidades, code smells, security hotspots, duplicación) se
corrige con la regla 5: DEF + fix/refactor + re-análisis.

---------------------------------------------------------------------------------
TAREA 4 – FASE 15: compuertas antes de desplegar (rama feature/ci)
---------------------------------------------------------------------------------
Amplía .github/workflows/ci.yml (ya existe con Ruff + pytest) a 8 jobs, un commit por job, cada
uno dependiente del anterior:
  ci: 1 estilo (ruff check y ruff format --check)
  ci: 2 pruebas por nivel (componente, integración, sistema, aceptación) con JUnit y
        cobertura ≥ 85 % (--cov=app --cov-report=xml para Sonar). Hoy la cobertura es ~98 %.
  ci: 3 sonar (SonarSource/sonarqube-scan-action en su versión actual; falla si el Quality Gate falla)
  ci: 4 mutantes (python scripts/verificar_mutantes.py)
  ci: 5 seguridad Trivy (aquasecurity/trivy-action, versión actual: fs, config e IMAGEN con
        docker build; falla con HIGH/CRITICAL). La imagen confirma DEF-018 (la imagen no trae pip).
  ci: 6 rendimiento (levanta uvicorn con --timeout-keep-alive 75, Locust 50 usuarios 60 s contra
        http://127.0.0.1:8000, python performance/verificar_umbrales.py ...)
  ci: 7 desplegar (solo en main, needs todos los anteriores, llama al secreto RENDER_DEPLOY_HOOK)
  ci: 8 humo (espera que APP_URL/salud responda la versión nueva)
Además:
  chore(render): render.yaml (runtime docker, plan free, healthCheckPath /salud, autoDeploy: false,
    ADMIN_TOKEN con generateValue, PERMITIR_SABOTAJE, MAX_PARTIDAS, PARTIDA_TTL_MINUTOS)
  feat(calidad): scripts/reporte_predespliegue.py → reportes/REPORTE_PREDESPLIEGUE.md con cada
    compuerta (estilo, niveles, cobertura, mutantes, Trivy, umbrales) y veredicto
    APTO PARA DESPLEGAR / NO DESPLEGAR (con sus pruebas de componente)
  test(sistemas): tests/integracion_sistemas/test_humo.py — solo corre si existe APP_URL
    (pytest.mark.skipif); verifica /salud, crear partida, unirse y 403 del panel admin.
    Nombres que ya promete el plan: test_flujo_basico_en_servidor_desplegado y
    test_panel_admin_desplegado_exige_token.
  ci: el job de compuertas sube REPORTE_PREDESPLIEGUE.md como artefacto (actions/upload-artifact)
  ci: el job desplegar crea un GitHub Release (v1.0.X) con el reporte adjunto y el enlace a la
      ejecución (permissions: contents: write)
  docs: docs/REGISTRO_DESPLIEGUES.md — tabla: fecha, versión, commit, veredicto, enlace al
      pipeline, quién aprobó
  docs: docs/API.md con la tabla de endpoints, mensajes de WebSocket y variables de entorno
      (el Modelo V de docs/CICLO_DE_VIDA.md ya lo menciona y todavía no existe)

---------------------------------------------------------------------------------
TAREA 5 – CIERRE
---------------------------------------------------------------------------------
1. En develop: ruff, pytest con cobertura, verificar_mutantes, Trivy y reporte_predespliegue
   → veredicto APTO.
2. git checkout main && git merge --no-ff develop -m "release: v1.0.0" && git tag v1.0.0 &&
   git push origin main develop --tags
3. Render (DETENTE y guía al humano): New → Blueprint → Trivia_Proyecto → URL; guardar en GitHub
   el secreto RENDER_DEPLOY_HOOK y la variable APP_URL; push a main → el pipeline debe llegar a
   "desplegar" y "humo" en verde.
4. Punto de quiebre CONTRA RENDER: set QUIEBRE_INICIO=10 && set QUIEBRE_INCREMENTO=10 &&
   set QUIEBRE_SEGUNDOS_ESCALON=20 y locust -f performance\punto_quiebre.py --host <APP_URL> ...
   + python performance\analizar_resultados.py quiebre_render; comparar con el local en
   docs/RESULTADOS_RENDIMIENTO.md (local: degradación 850 usuarios, sin quiebre hasta 1000, con
   la CPU del generador saturada desde ~600).
5. docs: EVIDENCIAS.md con enlaces a: Actions (la roja de v2: run 41956121926 y la verde de v3:
   run 41956454794), Quality Gate de Sonar, reportes de Trivy, gráficas de rendimiento, reporte
   pre-despliegue, DEFs y URL de Render.
6. Resumen final: total de commits (git rev-list --count --all), pruebas por nivel, cobertura,
   mutantes, Quality Gate, hallazgos de Trivy, DEF-001 a DEF-0XX, punto de quiebre local y en
   Render, URL y lo que falta.

---------------------------------------------------------------------------------
PENDIENTES MENORES (cuando sobre tiempo)
---------------------------------------------------------------------------------
- README: reemplazar "Integrante 2" e "Integrante 3" por los nombres reales del equipo.
- DEF-002: migrar del httpx del TestClient a httpx2 cuando se actualicen las dependencias.
- Mejora preventiva de DEF-016: limpiar antes las partidas en LOBBY sin jugadores.
- Revisar que los nombres de pruebas de la matriz de docs/PLAN_DE_PRUEBAS.md coincidan con los
  reales (p. ej. test_partida_inexistente_responde_404 está en tests/sistema/test_errores_http.py).

Empieza por: leer CLAUDE.md, preparar el entorno, correr pytest y verificar_mutantes, y decirme
qué tarea vamos a hacer. Al terminar cada tarea muéstrame el resumen y git log --oneline.
```

---

## Reparto sugerido

| Persona | Tareas | Necesita |
|---|---|---|
| Integrante 2 | Tarea 1 (DEF-019) y Tarea 2 (impacto del sabotaje) | Solo el repo |
| Integrante 3 | Tarea 3 (Sonar) y Tarea 4 (CI, render.yaml, reporte, humo, Release) | Cuenta de SonarCloud y acceso de escritura al repo (secretos) |
| Deivid | Tarea 5 (cierre, Render, punto de quiebre contra Render, EVIDENCIAS.md) | Cuenta de Render |

Las tareas 2 y 4 se pueden hacer en paralelo (tocan archivos distintos). La 5 va al final.
