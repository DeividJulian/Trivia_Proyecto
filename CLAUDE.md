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
    artefacto; el job `desplegar` crea un GitHub Release (v1.0.X) con el reporte adjunto y el enlace
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
| 15 | feature/ci | Pipeline de 8 jobs, render.yaml, reporte pre-despliegue, humo, registro de despliegues |
| Cierre | main | Release v1.0.0, Render, punto de quiebre contra Render, EVIDENCIAS.md |

## Estado actual

- **Fases terminadas:** 0, 1, 2, 3, 4 y 5 (integradas en `develop`).
- **En curso:** Fase 6 (`feature/partida`): clase `Partida` y `unirse` hechas.
- **Pruebas:** 63 en verde. **Defectos:** DEF-001 a DEF-007.
- **Pendiente del usuario:** instalar la extensión "SonarQube for IDE" en VS Code.
