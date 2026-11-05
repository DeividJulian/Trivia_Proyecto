# Ciclo de vida: Agile + DevOps

## Por qué Agile + DevOps

- **Incrementos por fase:** cada fase (configuración, modelos, puntaje, ranking, partida, API,
  Saboteador…) es un incremento pequeño en su propia rama `feature/`, que se integra a `develop`
  solo cuando sus pruebas pasan.
- **Retroalimentación rápida:** se desarrolla y se prueba a la vez; un commit = un cambio lógico.
- **CI/CD:** GitHub Actions ejecuta las compuertas (estilo, pruebas por nivel, Sonar, mutantes,
  Trivy y rendimiento) y solo despliega a Render desde `main` cuando todas pasan.
- **Cambios del cliente:** la solicitud de cambio del bono por velocidad (Fase 9) se atiende como
  un incremento más, con análisis de impacto y regresión.

Un modelo en cascada no encaja: el cliente (el profesor) pide cambios durante el proyecto y
necesitamos evidencia de calidad en cada incremento, no solo al final.

## Modelo V: cada etapa de desarrollo tiene su nivel de prueba

| Etapa de desarrollo (izquierda de la V) | Nivel de prueba (derecha de la V) | Dónde está |
|---|---|---|
| Requisitos (historias de usuario, RNF) | Aceptación | `docs/HISTORIAS_USUARIO.md` ↔ `tests/aceptacion/` |
| Diseño del sistema (API, estados de la partida) | Sistema | `docs/API.md` ↔ `tests/sistema/` |
| Arquitectura (capas dominio / API / tiempo real) | Integración | `app/dominio/partida.py`, `gestor.py` ↔ `tests/integracion/` |
| Código (funciones) | Componente | `app/dominio/puntaje.py`, `ranking.py` ↔ `tests/componente/` |
| Despliegue en Render | Integración de sistemas (humo) | `tests/integracion_sistemas/` |

## Dónde aplicamos shift-left

| Momento | Herramienta | Qué detecta |
|---|---|---|
| Mientras se escribe el código | SonarQube for IDE (antes SonarLint) | Bugs, code smells y vulnerabilidades en el editor |
| Antes de cada commit | pre-commit con Ruff | Estilo, imports, errores comunes y reglas de seguridad (S) |
| En cada push | GitHub Actions (CI) | Regresión, cobertura, mutantes, Trivy, Sonar y rendimiento |
| Antes de desplegar | `scripts/reporte_predespliegue.py` | Veredicto APTO PARA DESPLEGAR / NO DESPLEGAR |
