"""Pruebas de componente del registro de sabotajes (mutantes)."""

import pytest

from app.dominio import sabotajes
from app.dominio.sabotajes import Sabotaje

pytestmark = [pytest.mark.componente, pytest.mark.sabotajes]

PRUEBA = Sabotaje("de_prueba", "De prueba", "ninguno", "Solo para estas pruebas", "componente")


@pytest.fixture
def catalogo_de_prueba(monkeypatch):
    monkeypatch.setitem(sabotajes.CATALOGO, PRUEBA.clave, PRUEBA)
    sabotajes.desactivar_todos()


def test_activar_y_desactivar(catalogo_de_prueba):
    assert not sabotajes.esta_activo("de_prueba")

    sabotajes.activar("de_prueba")
    assert sabotajes.esta_activo("de_prueba")
    assert sabotajes.activos() == ["de_prueba"]

    sabotajes.desactivar("de_prueba")
    assert sabotajes.activos() == []


def test_desactivar_todos(catalogo_de_prueba):
    sabotajes.activar("de_prueba")

    sabotajes.desactivar_todos()

    assert sabotajes.activos() == []


def test_clave_desconocida_da_error_claro(catalogo_de_prueba):
    with pytest.raises(KeyError, match="Sabotaje desconocido: 'no_existe'"):
        sabotajes.activar("no_existe")


def test_lee_los_activos_de_la_variable_sabotajes(catalogo_de_prueba):
    claves = sabotajes.leer_activos_del_entorno(" de_prueba , ")

    assert claves == ["de_prueba"]
    assert sabotajes.esta_activo("de_prueba")


def test_variable_vacia_no_activa_nada(catalogo_de_prueba, monkeypatch):
    monkeypatch.delenv("SABOTAJES", raising=False)

    assert sabotajes.leer_activos_del_entorno() == []
    assert sabotajes.activos() == []
