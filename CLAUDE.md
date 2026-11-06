# CLAUDE.md – TestQuiz El Saboteador (backend)

Instrucciones permanentes para trabajar en este repositorio. Se actualiza al terminar cada fase.

## Proyecto

Backend de una trivia en vivo tipo Kahoot con **modo Saboteador**: mutantes controlados que se
activan desde un panel de administrador para demostrar que las pruebas detectan los errores
("efecto dominó"). Proyecto final de Pruebas y Mantenimiento de Software (UCC Pasto).
Exposición: **9 de noviembre de 2026**. El profesor revisa sobre todo las **pruebas antes del
despliegue** y los temas de clase: calidad, principios ISTQB, niveles, tipos, re-ejecución,
regresión, análisis de impacto, mantenimiento, rendimiento y punto de quiebre.

- Repositorio: https://github.com/DeividJulian/Trivia_Proyecto.git
- Carpeta local: `D:\Descargas\Trivia_Proyecto`
- Alcance: **solo backend** (Python 3.12, FastAPI, Pydantic v2, uvicorn, WebSockets). No hacer front.
- `app/dominio` **no** importa nada de FastAPI.

## Reglas

1. **Desarrollar y probar a la vez:** cada función o endpoint nuevo va seguido de sus pruebas en el
   commit siguiente (o antes, si la prueba va primero). Nunca acumular código sin probar.
2. **Commits pequeños y reales:** un commit = un cambio lógico. Nada de commits vacíos o de relleno.
   Conventional Commits en español: `feat`, `fix`, `test`, `docs`, `chore`, `ci`, `refactor`, `perf`.
3. Antes de cada commit: `ruff check .`, `ruff format --check .`, `pytest -q`. `git push` después
   de cada commit.
4. Git flow: `main ← develop ← feature/<nombre>`. Unir con `git merge --no-ff` y mensaje `merge: ...`.
5. **Ciclo de defectos** (detonante → intervención → confirmación → impacto → regresión): cada
   hallazgo de pytest, Ruff, SonarLint/SonarQube o Trivy se registra en `docs/REPORTE_DEFECTOS.md`
   como DEF-00X con: detectado por (herramienta y nivel), severidad, pasos para reproducir, causa
   (debugging), corrección, re-ejecución (confirmación), análisis de impacto, regresión y estado.
   La corrección va en su propio commit `fix(<módulo>): <qué> (DEF-00X)`. Falso positivo →
   "Riesgo aceptado" con justificación y `# noqa: <regla exacta>`; **nunca** desactivar reglas en bloque.
6. No cambiar un umbral ni borrar una prueba para que algo pase. Si algo falla, investigar la causa.
7. Nunca subir secretos (`.env`, `ADMIN_TOKEN`, `SONAR_TOKEN`, `RENDER_DEPLOY_HOOK`).
8. Comandos para CMD de Windows. Si el usuario debe actuar (iniciar sesión, una web, pegar un
   secreto), **detenerse** y explicarle paso a paso.
9. Al final de cada fase: arrancar el servidor (`set ADMIN_TOKEN=demo123 && uvicorn app.main:app`),
   probar lo nuevo en `/docs` y mostrar el resumen y `git log --oneline` de la fase.
10. **Bitácora de pruebas:** al terminar cada fase, agregar una fila en `docs/BITACORA_PRUEBAS.md`
    (fecha, fase, rama, qué se probó —nivel y tipo—, comando, resultado, cobertura, hallazgos de
    Ruff/SonarLint/Trivy y DEF creados). Datos reales, nunca inventados.
    Commit: `docs(bitacora): pruebas de la fase N`.
11. **Evidencias:** cuando Ruff, Trivy o pytest detecten algo, guardar la salida en
    `docs/evidencias/DEF-00X-antes.txt` y, tras corregir, en `DEF-00X-despues.txt`. Si el hallazgo
    viene de SonarLint en VS Code, **detenerse** y pedir al usuario una captura antes y después
    (`DEF-00X-antes.png` y `DEF-00X-despues.png`).
12. **Registro de despliegues (Fase 15):** el pipeline sube `REPORTE_PREDESPLIEGUE.md` como
    artefacto; el job `humo` (8 - Humo y release) crea el GitHub Release (v1.0.X) **solo después** de que
    el humo confirma que responde el commit recién desplegado, con el reporte adjunto y el enlace
    a la ejecución; `docs/REGISTRO_DESPLIEGUES.md` con fecha, versión, commit, veredicto, enlace al
    pipeline y quién aprobó.

## Convenciones del código

- Identificadores y textos en español, tal como los nombra el plan (`crear_app`, `calcular_puntos`, …).
- En `crear_app` usar `if gestor is None`, **nunca** `gestor or ...` (un gestor vacío tiene `len() == 0`).
- Tokens de prueba centralizados en `tests/valores_prueba.py` (DEF-005).
- Pruebas con totales de puntos exactos: responder **justo en el límite** de tiempo, para aislar
  base y racha del futuro bono por velocidad.
- Marcadores pytest: nivel (`componente`, `integracion`, `sistema`, `integracion_sistemas`,
  `aceptacion`), tipo (`no_funcional`, `seguridad`) y módulo (`puntaje`, `ranking`, `partida`,
  `gestor`, `api`, `sabotajes`).

## Fases

| Fase | Rama | Contenido |
|---|---|---|
| 0 | main | Arranque y shift-left (gitignore, requirements, pyproject, pre-commit, /salud) |
| 1 | feature/plan-pruebas | Plan de pruebas, principios, ciclo de vida, defectos, métricas, buenas prácticas |
| 2 | feature/configuracion | Configuracion, crear_app, cabeceras de seguridad |
| 3 | feature/modelos | Errores, EstadoPartida, Pregunta/Respuesta/Jugador, bancos de preguntas |
| 4 | feature/puntaje | Puntaje v1 (sin bono por velocidad) |
| 5 | feature/ranking | Ranking con desempates |
| 6 | feature/partida | Partida, conftest con RelojFalso, pruebas de integración, GestorPartidas |
| 7 | feature/api | API REST, WebSocket, pruebas de sistema funcionales y no funcionales |
| 8 | feature/aceptacion | Historias de usuario, pruebas de aceptación, pruebas exploratorias |
| 9 | feature/bono-velocidad | Solicitud de cambio, efecto dominó (tags v1-sin-bono, v2-cambio-con-error, v3-corregido), MANTENIMIENTO.md |
| 10 | feature/impacto | Análisis de impacto automatizado |
| 11 | feature/saboteador | Sabotajes (6 mutantes), panel admin, ejecutor y verificar_mutantes |
| 12 | feature/rendimiento | Locust, umbrales, punto de quiebre y gráficas |
| 13 | feature/seguridad | Dockerfile y Trivy |
| 14 | feature/sonar | SonarQube Cloud (requiere acción del usuario) |
| 15 | feature/ci | Pipeline de 8 etapas (la 3, SonarCloud, se agrega en la fase 14), render.yaml, reporte pre-despliegue, humo, release, registro de despliegues |
| Cierre | main | Release v1.0.0, Render, punto de quiebre contra Render, EVIDENCIAS.md |

## Estado actual

- **Carpeta del proyecto:** depende de la máquina. Deivid: `D:\Descargas\Trivia_Proyecto`; Jack:
  `C:\Users\Jack Limas\Universidad\Trivia_Proyecto`.
- **Fases terminadas:** 0 a 13 (integradas en `develop`). Tags: `v1-sin-bono`, `v2-cambio-con-error`, `v3-corregido`.
- **CI (`.github/workflows/ci.yml`):** jobs `1 - Estilo`, `2 - Pruebas y cobertura`, `3 - Sonar`, `4 - Mutantes`,
  `5 - Seguridad (Trivy)`, `6 - Rendimiento`, `7 - Reporte y despliegue` y `8 - Humo y release` (7 y 8 solo en
  `main`). El job 3 descarga `coverage.xml` del job 2, falla si el Quality Gate falla y sube `quality-gate.json`
  (`evidencias-sonar`), que el job 7 pasa al reporte predespliegue. Todas las acciones están fijadas por SHA (incidente GHSA-69fq-xp46-6x23 de trivy-action,
  19-03-2026) y la imagen base por digest; `.github/dependabot.yml` propone las actualizaciones contra `develop`
  (solo actúa cuando llegue a `main`).
- **Humo:** `/salud` devuelve `commit` (`RENDER_GIT_COMMIT` en Render, `APP_COMMIT` fuera de Render, `local` si
  no hay). El job 8 espera hasta 15 min a que `/salud` responda `github.sha`, corre `pytest -m integracion_sistemas`
  con `COMMIT_ESPERADO` y luego crea el release.
- **Render:** blueprint `render.yaml` con `autoDeploy: false`; la activación requiere
  `RENDER_DEPLOY_HOOK` como secreto y `APP_URL` como variable del repositorio.
- **Saboteador:** 6 mutantes en `app/dominio/sabotajes.py`; `scripts/verificar_mutantes.py` → 6/6.
  El ejecutor del panel lanza pytest dentro del servidor: la imagen Docker necesita `tests/`, `pytest` y `httpx`.
- **Rendimiento:** medición del 2026-11-04 (portátil de Deivid, solo REST): degradación 850, sin quiebre
  hasta 1000. Medición del 2026-11-06 (portátil de Jack, `docs/RESULTADOS_RENDIMIENTO.md`): REST vs. REST +
  WebSocket (`performance/locustfile_ws.py`, `punto_quiebre_ws.py`) en uvicorn local y en el contenedor;
  quiebre 600/550 (local) y 800/750 (contenedor), 0 % fallos. CPU con `performance/monitor_cpu.py` y
  comparación con `comparar_escenarios.py`. Las métricas de WebSocket van a `*_ws_eventos.csv`, no al p95 de
  Locust. No comparar mediciones de máquinas distintas. Servidor con `--timeout-keep-alive 75` (DEF-014);
  usar `127.0.0.1`, no `localhost`. `psutil` se importa dentro de las funciones (la imagen no lo trae).
- **Seguridad / imagen:** base `python:3.12-alpine` (DEF-025): `trivy image`, `trivy fs` y `trivy config` en 0
  HIGH/CRITICAL; la imagen quita pip (DEF-018) y corre como uid 10001. `test_reporte_predespliegue.py` está en
  `.dockerignore` porque importa `scripts/` (DEF-026): dentro del contenedor corren 277 pruebas; en el CI, 290.
  En la máquina de Jack hay Docker Desktop y Trivy 0.76.1 (en el PATH por WinGet); `docker build` se lanza desde
  CMD o PowerShell (desde Git Bash falla el helper de credenciales de Docker).
- **Front de demostración:** `app/static/` (HTML, CSS y JS sin dependencias),
  servido por FastAPI en `/`. Vistas: profesor, jugador y Saboteador (con tablero de dominó e impacto del sabotaje en vivo).
- **Impacto del sabotaje:** evaluación sombra (`sin_sabotajes`, `ranking_real`, `impacto_por_jugador`), endpoints `/api/admin/partidas` e `/impacto` y monitoreo en panel admin.
  Con varios sabotajes, el desglose usa una racha sombra por sabotaje (DEF-033, DEF-034): la suma del desglose
  de cada jugador es igual a su diferencia.
- **Ventana de daño:** `app/static/dano.html` + `dano.js` + `dano.css` (sin dependencias), enlazada desde el panel.
  Usa solo `/api/admin/partidas`, `/impacto` y `/sabotajes`; el token no se guarda en el navegador y no hay
  `innerHTML`. Pruebas en `tests/sistema/test_ventana_dano.py`; capturas `docs/evidencias/ventana-dano-*.png`.
  Playwright solo está instalado en el venv local (no en `requirements`).
- **SonarQube Cloud (fase 14):** organization `deividjulian`, projectKey `DeividJulian_Trivia_Proyecto`,
  Automatic Analysis desactivado, `SONAR_TOKEN` como secreto. `sonar-project.properties` en la raíz;
  `app/static/**` excluido solo de la cobertura (DEF-029). Quality Gate OK en `feature/sonar` (0 bugs,
  0 vulnerabilidades, 0 code smells, 0 hotspots, cobertura 97,6 %).
- **Trabajo actual:** falta el humo contra una URL desplegada (Render, con autorización).
- **Validación local de Fase 15:** 290 passed, 2 pruebas de humo omitidas sin `APP_URL`, cobertura
  97.53 %, mutantes 6/6, Ruff/format limpios; Locust 50 usuarios/60 s: p95 9 ms y 0 % fallos.
  Entorno local Python 3.11.9 (CI objetivo 3.12).
- **Bloque 1 (imagen Docker, 2026-11-05):** cerrado en local en la máquina de Jack (Python 3.12.10):
  290 passed, 2 skipped, cobertura 98 %. Confirmado en GitHub Actions (run 42161113908).
- **Bloque 2 (pipeline, 2026-11-06):** CI run 42168456389 en verde: 299 pruebas (3 omitidas sin `APP_URL`),
  cobertura 97,55 %, mutantes 6/6, Trivy 0/0/0, Locust p95 3 ms y 0 % fallos. Local: 296 passed, 3 skipped.
- **CI con Trivy v0.76.1** (input `version`, run 42170687291), igual que en local.
- **Bloque 3 (análisis adicional, 2026-11-06):** `docs/ANALISIS_ADICIONAL.md`. Bandit: 15 avisos ya tratados por
  los `noqa` de Ruff; Radon: CC media A, `Partida.responder` D (29) y 4 funciones C quedan como deuda técnica
  (sin refactor antes de la exposición); Vulture: DEF-027 y falsos positivos documentados; pip-audit: 0.
  Las 4 herramientas se instalan solo en local, no están en `requirements` ni en el CI.
  **Defectos:** DEF-001 a DEF-036. `Partida.responder` está en complejidad E (33): refactor pendiente tras la exposición.
