"""Pruebas de humo contra una aplicación desplegada en APP_URL."""

import os

import httpx
import pytest

APP_URL = os.environ.get("APP_URL", "").rstrip("/")

pytestmark = [
    pytest.mark.integracion_sistemas,
    pytest.mark.skipif(not APP_URL, reason="APP_URL no está configurada."),
]


def test_flujo_basico_en_servidor_desplegado():
    with httpx.Client(base_url=APP_URL, timeout=10.0) as cliente:
        salud = cliente.get("/salud")
        assert salud.status_code == 200
        assert salud.json()["estado"] == "ok"

        creada = cliente.post("/api/partidas")
        assert creada.status_code == 201
        partida = creada.json()
        pin = partida["pin"]
        cabeceras_host = {"X-Host-Token": partida["token_host"]}

        unida = cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Humo"})
        assert unida.status_code == 201

        iniciada = cliente.post(f"/api/partidas/{pin}/iniciar", headers=cabeceras_host)
        assert iniciada.status_code == 200
        assert iniciada.json()["estado"] == "PREGUNTA"


def test_panel_admin_desplegado_exige_token():
    with httpx.Client(base_url=APP_URL, timeout=10.0) as cliente:
        respuesta = cliente.get("/api/admin/partidas")

    assert respuesta.status_code == 403
