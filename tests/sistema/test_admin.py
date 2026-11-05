"""Pruebas de sistema del panel de administrador del Saboteador."""

import pytest
from fastapi.testclient import TestClient

from app.calidad import ejecutor
from app.calidad.ejecutor import Ejecucion, ResultadoPrueba
from app.config import Configuracion
from app.dominio import sabotajes
from app.main import crear_app
from tests.valores_prueba import OTRO_TOKEN_PRUEBA, TOKEN_ADMIN_PRUEBA

pytestmark = [pytest.mark.sistema, pytest.mark.api, pytest.mark.sabotajes]

ADMIN = {"X-Admin-Token": TOKEN_ADMIN_PRUEBA}
RUTAS_ADMIN = [
    ("get", "/api/admin/sabotajes"),
    ("post", "/api/admin/sabotajes/tiempo_estricto/activar"),
    ("post", "/api/admin/sabotajes/tiempo_estricto/desactivar"),
    ("post", "/api/admin/sabotajes/reparar"),
]


@pytest.fixture(autouse=True)
def sin_sabotajes():
    sabotajes.desactivar_todos()


# --- Seguridad ---------------------------------------------------------------------------------


@pytest.mark.seguridad
@pytest.mark.parametrize(("metodo", "ruta"), RUTAS_ADMIN)
def test_panel_sin_token_responde_403(cliente, metodo, ruta):
    respuesta = getattr(cliente, metodo)(ruta)

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "Token de administrador inválido."}
    assert sabotajes.activos() == []


@pytest.mark.seguridad
@pytest.mark.parametrize(("metodo", "ruta"), RUTAS_ADMIN)
def test_panel_con_token_incorrecto_responde_403(cliente, metodo, ruta):
    respuesta = getattr(cliente, metodo)(ruta, headers={"X-Admin-Token": OTRO_TOKEN_PRUEBA})

    assert respuesta.status_code == 403
    assert sabotajes.activos() == []


@pytest.mark.seguridad
@pytest.mark.parametrize("cabecera", ["", " "])
def test_admin_token_vacio_en_el_servidor_bloquea_el_panel(cabecera):
    with TestClient(crear_app(config=Configuracion(admin_token=""))) as cliente:
        respuesta = cliente.get("/api/admin/sabotajes", headers={"X-Admin-Token": cabecera})

    assert respuesta.status_code == 403


@pytest.mark.seguridad
def test_con_permitir_sabotaje_false_el_panel_no_existe():
    config = Configuracion(admin_token=TOKEN_ADMIN_PRUEBA, permitir_sabotaje=False)
    with TestClient(crear_app(config=config)) as cliente:
        respuesta = cliente.post("/api/admin/sabotajes/tiempo_estricto/activar", headers=ADMIN)

    assert respuesta.status_code == 404
    assert sabotajes.activos() == []


# --- Funcionamiento ----------------------------------------------------------------------------


def test_catalogo_con_los_6_mutantes(cliente):
    datos = cliente.get("/api/admin/sabotajes", headers=ADMIN).json()

    claves = {s["clave"] for s in datos["catalogo"]}
    assert claves == {
        "tiempo_estricto",
        "racha_no_suma",
        "bono_sin_acierto",
        "empates_mal",
        "no_guarda_respuesta",
        "respuesta_lenta",
    }
    assert all(s["nivel_que_lo_detecta"] for s in datos["catalogo"])
    assert datos["activos"] == []


def test_activar_y_desactivar(cliente):
    activado = cliente.post("/api/admin/sabotajes/empates_mal/activar", headers=ADMIN)
    assert activado.status_code == 200
    assert activado.json()["activos"] == ["empates_mal"]
    assert sabotajes.esta_activo("empates_mal")

    desactivado = cliente.post("/api/admin/sabotajes/empates_mal/desactivar", headers=ADMIN)
    assert desactivado.json()["activos"] == []


def test_reparar_desactiva_todos(cliente):
    for clave in ("tiempo_estricto", "racha_no_suma"):
        cliente.post(f"/api/admin/sabotajes/{clave}/activar", headers=ADMIN)

    reparado = cliente.post("/api/admin/sabotajes/reparar", headers=ADMIN)

    assert reparado.json()["activos"] == []
    assert sabotajes.activos() == []


def test_sabotaje_inexistente_responde_404(cliente):
    respuesta = cliente.post("/api/admin/sabotajes/borrar_todo/activar", headers=ADMIN)

    assert respuesta.status_code == 404


def test_activar_un_sabotaje_cambia_el_juego_de_verdad(cliente, partida_creada, reloj):
    """El mutante activado desde el panel afecta a una partida real (efecto visible en la demo)."""
    cliente.post("/api/admin/sabotajes/bono_sin_acierto/activar", headers=ADMIN)
    pin = partida_creada["pin"]
    cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Ana"})
    cliente.post(f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": partida_creada["token_host"]})

    reloj.avanzar(2.0)
    mala = cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": 3}).json()

    assert mala["puntos"] == 450  # con el sabotaje, una respuesta incorrecta suma bono


def test_el_log_registra_la_activacion(cliente, caplog):
    with caplog.at_level("WARNING", logger="testquiz.admin"):
        cliente.post("/api/admin/sabotajes/racha_no_suma/activar", headers=ADMIN)

    assert "Sabotaje ACTIVADO: racha_no_suma" in caplog.text


# --- Ejecución de pruebas desde el panel --------------------------------------------------------


@pytest.fixture
def ejecutor_falso(monkeypatch):
    """Evita lanzar pytest dentro de pytest: devuelve una ejecución simulada y guarda la llamada."""
    llamadas = []

    def falso(activos, argumentos):
        llamadas.append((activos, argumentos))
        resultados = [ResultadoPrueba("tests.x::test_racha", ("Puntaje",), "componente", True)]
        return Ejecucion(activos, 1, 0.5, resultados)

    monkeypatch.setattr(ejecutor, "ejecutar_pruebas", falso)
    return llamadas


def test_ejecutar_pruebas_devuelve_el_tablero(cliente, ejecutor_falso):
    cliente.post("/api/admin/sabotajes/racha_no_suma/activar", headers=ADMIN)

    respuesta = cliente.post("/api/admin/pruebas", headers=ADMIN)

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["sabotajes"] == ["racha_no_suma"]
    assert datos["tablero"]["modulos"]["Puntaje"]["estado"] == "CAIDO"
    assert datos["tablero"]["modulos"]["API"]["estado"] == "EN_RIESGO"
    assert ejecutor_falso == [(["racha_no_suma"], [])]


def test_ejecutar_solo_algunos_niveles(cliente, ejecutor_falso):
    cliente.post("/api/admin/pruebas", headers=ADMIN, json={"niveles": ["componente", "sistema"]})

    assert ejecutor_falso[0][1] == ["-m", "componente or sistema"]


def test_no_acepta_argumentos_libres_de_pytest(cliente, ejecutor_falso):
    respuesta = cliente.post("/api/admin/pruebas", headers=ADMIN, json={"niveles": ["-p evil"]})

    assert respuesta.status_code == 422
    assert ejecutor_falso == []


def test_candado_impide_dos_ejecuciones_a_la_vez(cliente, ejecutor_falso):
    candado = cliente.app.state.candado_pruebas
    cliente.portal.call(candado.acquire)
    try:
        respuesta = cliente.post("/api/admin/pruebas", headers=ADMIN)
    finally:
        candado.release()

    assert respuesta.status_code == 409
    assert ejecutor_falso == []


@pytest.mark.seguridad
def test_ejecutar_pruebas_sin_token_responde_403(cliente, ejecutor_falso):
    assert cliente.post("/api/admin/pruebas").status_code == 403
    assert ejecutor_falso == []
