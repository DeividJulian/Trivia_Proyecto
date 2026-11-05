"""Panel de administrador del modo Saboteador."""

import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

logger = logging.getLogger("testquiz.admin")


def verificar_admin(
    request: Request,
    x_admin_token: Annotated[str | None, Header(description="Token del panel (ADMIN_TOKEN).")] = None,
) -> None:
    """Protege todo el panel.

    404 si PERMITIR_SABOTAJE=false (el panel "no existe"); 403 si falta el token, si no coincide
    o si ADMIN_TOKEN está vacío en el servidor. La comparación es en tiempo constante.
    """
    config = request.app.state.config
    if not config.permitir_sabotaje:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El modo Saboteador está deshabilitado.")
    esperado = config.admin_token
    if (
        not esperado
        or not x_admin_token
        or not secrets.compare_digest(x_admin_token.encode(), esperado.encode())
    ):
        logger.warning(
            "Acceso denegado al panel de administrador desde %s.",
            request.client.host if request.client else "?",
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token de administrador inválido.")


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(verificar_admin)])
