"""Pruebas de sistema (funcionales) de la API REST."""

import pytest

from app.main import crear_app

pytestmark = [pytest.mark.sistema, pytest.mark.api]


def test_crear_partida_devuelve_pin_y_token(cliente):
    respuesta = cliente.post("/api/partidas")

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert len(datos["pin"]) == 6
    assert datos["token_host"]
    assert datos["estado"] == "LOBBY"


def test_crear_partida_con_categoria(cliente, gestor):
    respuesta = cliente.post("/api/partidas", json={"categoria": "cultura"})

    assert respuesta.status_code == 201


def test_ver_partida_no_expone_el_token(cliente, partida_creada):
    respuesta = cliente.get(f"/api/partidas/{partida_creada['pin']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "LOBBY"
    assert partida_creada["token_host"] not in respuesta.text


def test_gestor_inyectado_vacio_se_respeta(gestor):
    """Regresión del "gestor or ...": un gestor vacío es falso pero debe usarse igual."""
    assert len(gestor) == 0

    app = crear_app(gestor=gestor)

    assert app.state.gestor is gestor


def test_unirse_a_una_partida(cliente, partida_creada):
    pin = partida_creada["pin"]

    respuesta = cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "  Ana "})

    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == "Ana"
    assert cliente.get(f"/api/partidas/{pin}").json()["jugadores"] == ["Ana"]


def test_unirse_con_nombre_repetido_responde_409(cliente, partida_creada):
    url = f"/api/partidas/{partida_creada['pin']}/jugadores"
    cliente.post(url, json={"nombre": "Ana"})

    respuesta = cliente.post(url, json={"nombre": "ana"})

    assert respuesta.status_code == 409
    assert "Ya hay un jugador" in respuesta.json()["detail"]


def test_anfitrion_inicia_y_avanza_la_partida(cliente, partida_creada):
    pin, token = partida_creada["pin"], partida_creada["token_host"]
    cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Ana"})
    cabeceras = {"X-Host-Token": token}

    iniciada = cliente.post(f"/api/partidas/{pin}/iniciar", headers=cabeceras)
    assert iniciada.status_code == 200
    assert iniciada.json()["estado"] == "PREGUNTA"
    assert "correcta" not in iniciada.json()

    resultados = cliente.post(f"/api/partidas/{pin}/siguiente", headers=cabeceras)
    assert resultados.json()["estado"] == "RESULTADOS"
    assert resultados.json()["correcta"] == 0


def test_iniciar_sin_token_responde_403(cliente, partida_creada):
    pin = partida_creada["pin"]
    cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": "Ana"})

    respuesta = cliente.post(f"/api/partidas/{pin}/iniciar")

    assert respuesta.status_code == 403
    assert cliente.get(f"/api/partidas/{pin}").json()["estado"] == "LOBBY"


def test_responder_y_consultar_el_marcador(cliente, partida_creada, reloj):
    pin, token = partida_creada["pin"], partida_creada["token_host"]
    for nombre in ("Ana", "Beto"):
        cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": nombre})
    cliente.post(f"/api/partidas/{pin}/iniciar", headers={"X-Host-Token": token})
    reloj.avanzar(20.0)

    respuesta = cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": 0})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"nombre": "Ana", "puntos": 1000, "racha": 1, "puntos_totales": 1000}
    marcador = cliente.get(f"/api/partidas/{pin}/jugadores/Ana").json()
    assert marcador["posicion"] == 1
    assert marcador["respondio_pregunta_actual"] is True


def test_jugador_inexistente_responde_404(cliente, partida_creada):
    respuesta = cliente.get(f"/api/partidas/{partida_creada['pin']}/jugadores/Nadie")

    assert respuesta.status_code == 404
    assert "Nadie" in respuesta.json()["detail"]


# --- Extremo a extremo ---------------------------------------------------------------------------


def test_partida_completa_de_extremo_a_extremo(cliente, reloj):
    """Crear → unirse → iniciar → responder cada pregunta → resultados → podio, solo por HTTP."""
    creada = cliente.post("/api/partidas").json()
    pin, host = creada["pin"], {"X-Host-Token": creada["token_host"]}
    for nombre in ("Ana", "Beto"):
        assert cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": nombre}).status_code == 201
    assert cliente.post(f"/api/partidas/{pin}/iniciar", headers=host).json()["estado"] == "PREGUNTA"

    total = cliente.get(f"/api/partidas/{pin}").json()["total_preguntas"]
    for numero in range(total):
        correcta = numero % 4
        reloj.avanzar(20.0)  # justo en el límite: los totales dependen solo de base y racha
        cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": correcta})
        incorrecta = (correcta + 1) % 4
        cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Beto", "opcion": incorrecta})
        estado = cliente.get(f"/api/partidas/{pin}").json()
        assert estado["estado"] == "RESULTADOS"
        assert estado["correcta"] == correcta
        cliente.post(f"/api/partidas/{pin}/siguiente", headers=host)

    final = cliente.get(f"/api/partidas/{pin}").json()
    assert final["estado"] == "FINALIZADA"
    assert final["ganador"]["nombre"] == "Ana"
    assert final["ganador"]["puntos"] == 1000 + 1100 + 1200
    assert [fila["nombre"] for fila in final["ranking"]] == ["Ana", "Beto"]
    assert final["ranking"][1]["puntos"] == 0
