# Buenas prácticas del equipo

## Git flow

```
main      ← solo versiones aptas para desplegar (tags v1.0.0, ...)
develop   ← integración de las funcionalidades terminadas y probadas
feature/* ← una rama por funcionalidad o fase (feature/puntaje, feature/api, ...)
```

- Cada rama `feature/` sale de `develop` y vuelve con `git merge --no-ff` y mensaje `merge: ...`,
  para que el historial muestre cuándo entró cada incremento.
- Nunca se hace commit directo a `main` después del arranque.

## Conventional Commits (en español)

| Tipo | Uso | Ejemplo |
|---|---|---|
| `feat` | Funcionalidad nueva | `feat(puntaje): calcular_puntos(...)` |
| `fix` | Corrección de un defecto (con su DEF) | `fix(puntaje): el bono solo aplica a respuestas correctas (DEF-004)` |
| `test` | Pruebas nuevas o corregidas | `test(ranking): desempate por tiempo y por nombre` |
| `docs` | Documentación | `docs: PLAN_DE_PRUEBAS.md` |
| `chore` | Configuración y herramientas | `chore: pyproject.toml con Ruff y pytest` |
| `ci` | Pipeline de GitHub Actions | `ci: 1 estilo` |
| `refactor` | Cambio interno sin cambiar el comportamiento | `refactor(main): fábrica crear_app` |
| `perf` | Mejora de rendimiento | `perf(api): ...` |

Un commit = un cambio lógico pequeño que deja el proyecto funcionando (ruff y pytest en verde).

## Revisión de PR por otro integrante (independencia)

Quien escribe el código no es quien lo aprueba: el PR de `feature/*` a `develop` lo revisa otro
integrante. ISTQB recomienda **independencia** porque el autor tiene sesgo de confirmación (tiende
a probar lo que espera que funcione). El revisor comprueba que:

1. Cada función nueva tiene su prueba y el CI está en verde.
2. Si hubo un defecto, existe su DEF con re-ejecución y regresión.
3. No se bajó ningún umbral ni se borró ninguna prueba para "hacer pasar" el CI.

## Análisis estático

- **Ruff** (pre-commit y CI) con las reglas E, F, I, B, UP, SIM, N y S (seguridad).
- **SonarQube for IDE** mientras se programa y **SonarQube Cloud** en el CI (Quality Gate).
- **Trivy** para dependencias, secretos y configuración del Dockerfile.
- Un falso positivo se acepta con `# noqa: <regla>` y su DEF; nunca se desactivan reglas en bloque.

## Secretos

- `.env` está en `.gitignore`; solo se sube `.env.example` sin valores.
- `ADMIN_TOKEN`, `SONAR_TOKEN` y `RENDER_DEPLOY_HOOK` viven en los secretos de GitHub o en Render
  (`generateValue`), nunca en el código ni en los logs.
- Los tokens se comparan con `secrets.compare_digest` para evitar ataques de tiempo.

## Arquitectura por capas

```
app/api/          → HTTP y WebSocket (FastAPI, esquemas Pydantic). Traduce errores a 404/403/409.
app/tiempo_real/  → Conexiones WebSocket y difusión del estado.
app/dominio/      → Reglas del juego (puntaje, ranking, partida, gestor). NO importa FastAPI.
app/calidad/      → Análisis de impacto y ejecutor de pruebas del Saboteador.
```

El dominio no depende de la web: se prueba a nivel de componente sin servidor y se puede cambiar la
capa de transporte sin tocar las reglas.

## Inyección de dependencias

- `Partida` recibe el **reloj** por parámetro (por defecto `time.monotonic`): las pruebas usan un
  `RelojFalso` y controlan el tiempo sin `sleep`.
- `crear_app(gestor=None, admin_token=None, config=None)` permite crear la aplicación con un gestor
  y una configuración de prueba. Se usa `if gestor is None` y no `gestor or ...`, porque un gestor
  vacío tiene `len() == 0` y Python lo trataría como falso.
