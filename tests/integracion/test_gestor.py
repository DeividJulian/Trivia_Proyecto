"""Pruebas de integración de componentes: GestorPartidas + Partida + Preguntas."""

import pytest

from app.dominio import gestor as modulo_gestor
from app.dominio.errores import AccesoDenegado, ErrorPartida, PartidaNoEncontrada
from app.dominio.gestor import GestorPartidas
from app.dominio.modelos import EstadoPartida
from tests.conftest import RelojFalso, crear_preguntas

pytestmark = [pytest.mark.integracion, pytest.mark.gestor]


@pytest.fixture
def gestor(reloj) -> GestorPartidas:
    return GestorPartidas(reloj=reloj, cargador=lambda _categoria: crear_preguntas(), max_partidas=3)


def test_crea_partida_con_pin_de_6_digitos_y_token(gestor):
    partida, token = gestor.crear()

    assert len(partida.pin) == 6
    assert partida.pin.isdigit()
    assert len(token) >= 32
    assert gestor.obtener(partida.pin) is partida
    assert len(gestor) == 1


def test_pin_unico_aunque_el_azar_se_repita(gestor, monkeypatch):
    valores = iter([42, 42, 7])
    monkeypatch.setattr(modulo_gestor.secrets, "randbelow", lambda _n: next(valores))

    primera, _ = gestor.crear()
    segunda, _ = gestor.crear()

    assert primera.pin == "000042"
    assert segunda.pin == "000007"


def test_cada_partida_tiene_su_propio_token(gestor):
    _, token_a = gestor.crear()
    _, token_b = gestor.crear()

    assert token_a != token_b


def test_pin_inexistente_lanza_partida_no_encontrada(gestor):
    with pytest.raises(PartidaNoEncontrada, match="999999"):
        gestor.obtener("999999")


def test_token_valido_devuelve_la_partida(gestor):
    partida, token = gestor.crear()

    assert gestor.validar_host(partida.pin, token) is partida


@pytest.mark.parametrize("token", ["", None, "token-falso"])
def test_token_invalido_lanza_acceso_denegado(gestor, token):
    partida, _ = gestor.crear()

    with pytest.raises(AccesoDenegado):
        gestor.validar_host(partida.pin, token)


def test_token_de_otra_partida_no_sirve(gestor):
    partida_a, _ = gestor.crear()
    _, token_b = gestor.crear()

    with pytest.raises(AccesoDenegado):
        gestor.validar_host(partida_a.pin, token_b)


def test_limite_de_partidas_con_mensaje_claro(gestor):
    for _ in range(3):
        gestor.crear()

    with pytest.raises(ErrorPartida, match="máximo de 3 partidas"):
        gestor.crear()


def test_gestor_vacio_es_falso_pero_no_es_none():
    """Documenta por qué crear_app usa "if gestor is None" y no "gestor or ...": len() == 0."""
    vacio = GestorPartidas()

    assert len(vacio) == 0
    assert not vacio
    assert vacio is not None


def test_limpieza_de_partidas_inactivas(gestor, reloj):
    vieja, _ = gestor.crear()
    reloj.avanzar(20 * 60)
    nueva, _ = gestor.crear()
    reloj.avanzar(10 * 60 + 1)

    assert gestor.limpiar() == 1
    with pytest.raises(PartidaNoEncontrada):
        gestor.obtener(vieja.pin)
    assert gestor.obtener(nueva.pin) is nueva


def test_la_actividad_mantiene_viva_la_partida(gestor, reloj):
    partida, _ = gestor.crear()
    reloj.avanzar(29 * 60)
    partida.unirse("Ana")
    reloj.avanzar(29 * 60)

    assert gestor.limpiar() == 0


def test_partida_finalizada_se_limpia_antes(gestor, reloj):
    partida, _ = gestor.crear()
    partida.unirse("Ana")
    partida.iniciar()
    while partida.estado != EstadoPartida.FINALIZADA:
        partida.siguiente()

    reloj.avanzar(5 * 60 + 1)

    assert gestor.limpiar() == 1


def test_limpiar_libera_cupo_para_crear(reloj):
    gestor = GestorPartidas(reloj=reloj, cargador=lambda _c: crear_preguntas(), max_partidas=1, ttl_minutos=1)
    gestor.crear()
    reloj.avanzar(61)

    partida, _ = gestor.crear()

    assert len(gestor) == 1
    assert gestor.obtener(partida.pin) is partida


def test_usa_el_banco_de_preguntas_real_por_categoria():
    gestor = GestorPartidas(reloj=RelojFalso())

    partida, _ = gestor.crear("cultura")

    assert len(partida.preguntas) == 12
