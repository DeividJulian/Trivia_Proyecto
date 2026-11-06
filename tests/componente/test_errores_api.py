"""Pruebas de componente de la traducción de errores del dominio a códigos HTTP."""

import pytest

from app.api.errores import codigo_para
from app.dominio.errores import AccesoDenegado, ErrorPartida, PartidaNoEncontrada

pytestmark = [pytest.mark.componente, pytest.mark.api]


@pytest.mark.parametrize(
    ("error", "codigo"),
    [
        (PartidaNoEncontrada("123456"), 404),
        (AccesoDenegado(), 403),
        (ErrorPartida("estado inválido"), 409),
    ],
)
def test_cada_error_del_dominio_tiene_su_codigo(error, codigo):
    assert codigo_para(error) == codigo


def test_partida_no_encontrada_menciona_el_pin():
    assert "123456" in str(PartidaNoEncontrada("123456"))
