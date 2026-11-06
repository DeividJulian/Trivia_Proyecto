"""Punto de entrada de la aplicación FastAPI."""

import asyncio
import logging
from dataclasses import replace
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from app.api import admin, rutas, ws
from app.api.errores import registrar_manejadores
from app.config import VERSION, Configuracion, cargar_configuracion
from app.dominio.gestor import GestorPartidas
from app.tiempo_real.conexiones import GestorConexiones

__all__ = ["VERSION", "app", "crear_app"]

DIRECTORIO_FRONT = Path(__file__).resolve().parent / "static"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("testquiz")

CABECERAS_SEGURIDAD = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def crear_app(
    gestor: GestorPartidas | None = None,
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
    if not config.admin_token:
        logger.warning("ADMIN_TOKEN no está configurado: el panel de administrador queda bloqueado.")

    if gestor is None:
        gestor = GestorPartidas(max_partidas=config.max_partidas, ttl_minutos=config.partida_ttl_minutos)

    app = FastAPI(title="TestQuiz – El Saboteador", version=VERSION)
    app.state.config = config
    app.state.gestor = gestor
    app.state.conexiones = GestorConexiones()
    app.state.candado_pruebas = asyncio.Lock()
    registrar_manejadores(app)
    app.include_router(rutas.router)
    app.include_router(ws.router)
    app.include_router(admin.router)

    @app.middleware("http")
    async def cabeceras_seguridad(request: Request, call_next) -> Response:
        """Agrega cabeceras de seguridad básicas a todas las respuestas HTTP."""
        respuesta = await call_next(request)
        for nombre, valor in CABECERAS_SEGURIDAD.items():
            respuesta.headers.setdefault(nombre, valor)
        return respuesta

    @app.get("/salud", tags=["salud"])
    def salud() -> dict:
        """Indica que el servicio está en pie, qué versión corre y de qué commit es el despliegue."""
        return {"estado": "ok", "version": VERSION, "commit": config.commit}

    # El front de demostración se monta al final: las rutas de la API y /docs tienen prioridad.
    if DIRECTORIO_FRONT.is_dir():
        app.mount("/", StaticFiles(directory=DIRECTORIO_FRONT, html=True), name="front")

    return app


app = crear_app()
