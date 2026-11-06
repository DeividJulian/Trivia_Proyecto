"""Pruebas de aceptación: una por historia de usuario (docs/HISTORIAS_USUARIO.md).

Solo usan la API pública (HTTP y WebSocket) con el reloj real y el banco de preguntas real.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Configuracion
from app.main import crear_app
from tests.valores_prueba import TOKEN_ADMIN_PRUEBA

pytestmark = pytest.mark.aceptacion

BANCO = Path(__file__).resolve().parents[2] / "data" / "preguntas.json"
CLAVE = [pregunta["correcta"] for pregunta in json.loads(BANCO.read_text(encoding="utf-8"))]


@pytest.fixture
def api():
    with TestClient(crear_app(config=Configuracion(admin_token=TOKEN_ADMIN_PRUEBA))) as cliente:
        yield cliente


class Profesor:
    def __init__(self, api: TestClient) -> None:
        self.api = api
        creada = api.post("/api/partidas").json()
        self.pin = creada["pin"]
        self._host = {"X-Host-Token": creada["token_host"]}

    def iniciar(self):
        return self.api.post(f"/api/partidas/{self.pin}/iniciar", headers=self._host)

    def avanzar(self):
        return self.api.post(f"/api/partidas/{self.pin}/siguiente", headers=self._host)

    def estado(self) -> dict:
        return self.api.get(f"/api/partidas/{self.pin}").json()


class Estudiante:
    def __init__(self, api: TestClient, pin: str, nombre: str) -> None:
        self.api, self.pin, self.nombre = api, pin, nombre

    def unirse(self):
        return self.api.post(f"/api/partidas/{self.pin}/jugadores", json={"nombre": self.nombre})

    def responder(self, opcion: int):
        return self.api.post(
            f"/api/partidas/{self.pin}/respuestas", json={"nombre": self.nombre, "opcion": opcion}
        )

    def marcador(self) -> dict:
        return self.api.get(f"/api/partidas/{self.pin}/jugadores/{self.nombre}").json()


def incorrecta(numero: int) -> int:
    return (CLAVE[numero] + 1) % 4


def test_hu01_profesor_crea_partida_y_tres_estudiantes_juegan(api):
    profesor = Profesor(api)
    estudiantes = [Estudiante(api, profesor.pin, nombre) for nombre in ("Ana", "Beto", "Caro")]

    for estudiante in estudiantes:
        assert estudiante.unirse().status_code == 201
    assert profesor.estado()["estado"] == "LOBBY"
    assert profesor.estado()["jugadores"] == ["Ana", "Beto", "Caro"]

    assert profesor.iniciar().status_code == 200
    for numero in range(len(CLAVE)):
        for posicion, estudiante in enumerate(estudiantes):
            opcion = CLAVE[numero] if posicion != 2 else incorrecta(numero)
            assert estudiante.responder(opcion).status_code == 200
        assert profesor.estado()["estado"] == "RESULTADOS"
        profesor.avanzar()

    final = profesor.estado()
    assert final["estado"] == "FINALIZADA"
    assert len(final["ranking"]) == 3
    assert final["ganador"]["nombre"] in {"Ana", "Beto"}
    assert final["ranking"][-1]["nombre"] == "Caro"


def test_hu02_gana_quien_responde_bien(api):
    profesor = Profesor(api)
    sabe = Estudiante(api, profesor.pin, "Sabe")
    adivina = Estudiante(api, profesor.pin, "Adivina")
    sabe.unirse()
    adivina.unirse()
    profesor.iniciar()

    for numero in range(3):
        sabe.responder(CLAVE[numero])
        adivina.responder(incorrecta(numero))
        profesor.avanzar()
        assert sabe.marcador()["racha"] == numero + 1

    assert adivina.marcador()["puntos"] == 0
    assert sabe.marcador()["posicion"] == 1
    assert sabe.marcador()["puntos"] > 0


def test_hu03_no_se_puede_responder_dos_veces(api):
    profesor = Profesor(api)
    ana, beto = Estudiante(api, profesor.pin, "Ana"), Estudiante(api, profesor.pin, "Beto")
    ana.unirse()
    beto.unirse()
    profesor.iniciar()

    ana.responder(CLAVE[0])
    puntos = ana.marcador()["puntos"]
    segunda = ana.responder(CLAVE[0])

    assert segunda.status_code == 409
    assert ana.marcador()["puntos"] == puntos

    profesor.avanzar()  # cierra la pregunta
    assert beto.responder(CLAVE[0]).status_code == 409


def test_hu04_solo_el_profesor_controla_la_partida(api):
    profesor = Profesor(api)
    Estudiante(api, profesor.pin, "Ana").unirse()

    sin_token = api.post(f"/api/partidas/{profesor.pin}/iniciar")
    assert sin_token.status_code == 403
    assert profesor.estado()["estado"] == "LOBBY"

    profesor.iniciar()
    falso = api.post(f"/api/partidas/{profesor.pin}/siguiente", headers={"X-Host-Token": "soy-el-profe"})
    assert falso.status_code == 403
    assert profesor.estado()["estado"] == "PREGUNTA"
    assert profesor.estado()["numero_pregunta"] == 1


def test_hu05_ver_la_partida_en_vivo(api):
    profesor = Profesor(api)
    ana = Estudiante(api, profesor.pin, "Ana")
    ana.unirse()

    with api.websocket_connect(f"/ws/{profesor.pin}") as pantalla_de_ana:
        assert pantalla_de_ana.receive_json()["datos"]["jugadores"] == ["Ana"]

        Estudiante(api, profesor.pin, "Beto").unirse()
        assert pantalla_de_ana.receive_json()["datos"]["jugadores"] == ["Ana", "Beto"]

        profesor.iniciar()
        en_vivo = pantalla_de_ana.receive_json()["datos"]
        assert en_vivo["estado"] == "PREGUNTA"
        assert en_vivo["pregunta"]["texto"]
        assert "correcta" not in en_vivo
