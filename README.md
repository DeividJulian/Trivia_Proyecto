# TestQuiz – El Saboteador

Backend de una trivia en vivo al estilo Kahoot con un **modo Saboteador**: mutantes controlados que
se activan desde un panel de administrador para demostrar que las pruebas detectan los errores
(el "efecto dominó").

## Objetivo del proyecto

Proyecto final de **Pruebas y Mantenimiento de Software** (Universidad Cooperativa de Colombia,
sede Pasto). El objetivo no es solo que el juego funcione, sino **obtener evidencia, antes de
desplegar, de que funciona correctamente**: pruebas por nivel y tipo (ISTQB), análisis estático,
análisis de impacto, regresión, mutantes, rendimiento, punto de quiebre y seguridad.

Exposición: 9 de noviembre de 2026.

## Equipo

| Integrante | Rol principal |
|---|---|
| Deivid Julián Alvarado | Desarrollo backend y automatización de pruebas |
| Integrante 2 | Plan de pruebas, aceptación y pruebas exploratorias |
| Integrante 3 | Rendimiento, seguridad y despliegue |

## Tecnologías

Python 3.12 · FastAPI · Pydantic v2 · Uvicorn · WebSockets

## Ejecutar en local (CMD de Windows)

```cmd
cd D:\Descargas\Trivia_Proyecto
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
set ADMIN_TOKEN=demo123
uvicorn app.main:app --port 8000 --timeout-keep-alive 75
```

- Front de demostración: <http://127.0.0.1:8000/>
  - **Profesor:** crea la partida, muestra el PIN, inicia y avanza las preguntas.
  - **Jugador:** se une con el PIN (abrir en otra pestaña o en el celular, misma red) y responde.
  - **Saboteador:** con el token `demo123` activa mutantes y ejecuta las pruebas (tablero de dominó).
- Documentación de la API: <http://127.0.0.1:8000/docs>
- Pruebas: `pytest -q` · mutantes: `python scripts\verificar_mutantes.py`
