"""Punto de entrada de la aplicación FastAPI."""

from dataclasses import replace
from typing import Any

from fastapi import FastAPI

from app.config import VERSION, Configuracion, cargar_configuracion

__all__ = ["VERSION", "app", "crear_app"]


def crear_app(
    gestor: Any = None,
    admin_token: str | None = None,
    config: Configuracion | None = None,
) -> FastAPI:
    """Fábrica de la aplicación: permite inyectar el gestor, el token de administrador o la configuración.

    Se usa "is None" y nunca "gestor or ...": un gestor sin partidas tiene len() == 0 y
    Python lo trataría como falso, reemplazando el gestor inyectado por uno nuevo.
    """
    if config is None:
        config = cargar_configuracion()
    if admin_token is not None:
        config = replace(config, admin_token=admin_token)

    app = FastAPI(title="TestQuiz – El Saboteador", version=VERSION)
    app.state.config = config
    app.state.gestor = gestor

    @app.get("/salud", tags=["salud"])
    def salud() -> dict:
        """Indica que el servicio está en pie y qué versión corre."""
        return {"estado": "ok", "version": VERSION}

    return app


app = crear_app()
