"""Punto de entrada de la aplicación FastAPI."""

from fastapi import FastAPI

VERSION = "1.0.0"

app = FastAPI(title="TestQuiz – El Saboteador", version=VERSION)


@app.get("/salud", tags=["salud"])
def salud() -> dict:
    """Indica que el servicio está en pie y qué versión corre."""
    return {"estado": "ok", "version": VERSION}
