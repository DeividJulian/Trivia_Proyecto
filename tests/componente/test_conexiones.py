"""Pruebas de componente del GestorConexiones con sockets falsos."""

import asyncio

import pytest

from app.tiempo_real.conexiones import GestorConexiones

pytestmark = [pytest.mark.componente, pytest.mark.api]


class SocketFalso:
    def __init__(self, cerrado: bool = False) -> None:
        self.cerrado = cerrado
        self.recibidos: list = []

    async def send_json(self, data) -> None:
        if self.cerrado:
            raise RuntimeError("socket cerrado")
        self.recibidos.append(data)


def test_conectar_desconectar_y_total():
    conexiones = GestorConexiones()
    a, b, c = SocketFalso(), SocketFalso(), SocketFalso()
    conexiones.conectar("111111", a)
    conexiones.conectar("111111", b)
    conexiones.conectar("222222", c)

    assert conexiones.total() == 3
    assert conexiones.total("111111") == 2

    conexiones.desconectar("111111", a)
    conexiones.desconectar("111111", b)
    conexiones.desconectar("999999", c)  # PIN sin sockets: no falla

    assert conexiones.total("111111") == 0
    assert conexiones.total() == 1


def test_difundir_solo_a_la_partida_indicada():
    conexiones = GestorConexiones()
    a, otro = SocketFalso(), SocketFalso()
    conexiones.conectar("111111", a)
    conexiones.conectar("222222", otro)

    entregados = asyncio.run(conexiones.difundir("111111", {"tipo": "estado"}))

    assert entregados == 1
    assert a.recibidos == [{"tipo": "estado"}]
    assert otro.recibidos == []


def test_difundir_limpia_sockets_cerrados_sin_afectar_a_los_demas():
    conexiones = GestorConexiones()
    vivo1, cerrado, vivo2 = SocketFalso(), SocketFalso(cerrado=True), SocketFalso()
    for socket in (vivo1, cerrado, vivo2):
        conexiones.conectar("111111", socket)

    entregados = asyncio.run(conexiones.difundir("111111", {"n": 1}))

    assert entregados == 2
    assert vivo1.recibidos == vivo2.recibidos == [{"n": 1}]
    assert conexiones.total("111111") == 2


def test_difundir_a_partida_sin_sockets():
    assert asyncio.run(GestorConexiones().difundir("000000", {})) == 0
