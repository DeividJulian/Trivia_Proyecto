"""Pruebas de sistema (funcionales, negativas) de los códigos de error de la API."""

import pytest

pytestmark = [pytest.mark.sistema, pytest.mark.api]


def preparar(cliente, partida_creada, iniciar=False):
    pin = partida_creada["pin"]
    cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Ana"})
    if iniciar:
        cliente.post(f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": partida_creada["token_host"]})
    return pin


# --- 404 ---------------------------------------------------------------------------------------


def test_partida_inexistente_responde_404(cliente):
    respuesta = cliente.get("/api/partidas/000000")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "No existe una partida con el PIN 000000."}


@pytest.mark.parametrize(
    ("metodo", "ruta", "cuerpo"),
    [
        ("post", "/api/partidas/000000/jugadores", {"nombre": "Ana"}),
        ("post", "/api/partidas/000000/respuestas", {"nombre": "Ana", "opcion": 0}),
        ("post", "/api/partidas/000000/iniciar", None),
        ("post", "/api/partidas/000000/siguiente", None),
        ("get", "/api/partidas/000000/jugadores/Ana", None),
    ],
)
def test_todas_las_rutas_responden_404_con_pin_inexistente(cliente, metodo, ruta, cuerpo):
    respuesta = getattr(cliente, metodo)(ruta, **({"json": cuerpo} if cuerpo else {}))

    assert respuesta.status_code == 404
    assert "detail" in respuesta.json()


# --- 403 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("accion", ["iniciar", "siguiente"])
@pytest.mark.parametrize("cabeceras", [{}, {"X-Host-Token": "token-falso"}])
def test_acciones_del_anfitrion_sin_token_valido_responden_403(cliente, partida_creada, accion, cabeceras):
    pin = preparar(cliente, partida_creada)

    respuesta = cliente.post(f"/api/partidas/{pin}/{accion}", headers=cabeceras)

    assert respuesta.status_code == 403
    assert "Token de anfitrión inválido" in respuesta.json()["detail"]


# --- 409 ---------------------------------------------------------------------------------------


def test_iniciar_sin_jugadores_responde_409(cliente, partida_creada):
    pin = partida_creada["pin"]

    respuesta = cliente.post(
        f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": partida_creada["token_host"]}
    )

    assert respuesta.status_code == 409
    assert "al menos un jugador" in respuesta.json()["detail"]


def test_responder_dos_veces_responde_409(cliente, partida_creada):
    pin = preparar(cliente, partida_creada)
    cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Beto"})
    cliente.post(f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": partida_creada["token_host"]})
    cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": 0})

    respuesta = cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": 1})

    assert respuesta.status_code == 409


def test_responder_en_lobby_responde_409(cliente, partida_creada):
    pin = preparar(cliente, partida_creada)

    respuesta = cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": 0})

    assert respuesta.status_code == 409


def test_unirse_a_partida_iniciada_responde_409(cliente, partida_creada):
    pin = preparar(cliente, partida_creada, iniciar=True)

    respuesta = cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Tarde"})

    assert respuesta.status_code == 409


# --- 422 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("opcion", [-1, 4, "a"])
def test_opcion_fuera_de_0_a_3_responde_422(cliente, partida_creada, opcion):
    pin = preparar(cliente, partida_creada, iniciar=True)

    respuesta = cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": opcion})

    assert respuesta.status_code == 422


@pytest.mark.parametrize("nombre", ["", "x" * 21])
def test_nombre_fuera_de_1_a_20_responde_422(cliente, partida_creada, nombre):
    respuesta = cliente.post(f"/api/partidas/{partida_creada['pin']}/jugadores", json={"nombre": nombre})

    assert respuesta.status_code == 422


def test_categoria_inexistente_responde_422(cliente):
    assert cliente.post("/api/partidas", json={"categoria": "deportes"}).status_code == 422


def test_cuerpo_faltante_responde_422(cliente, partida_creada):
    assert cliente.post(f"/api/partidas/{partida_creada['pin']}/jugadores").status_code == 422
