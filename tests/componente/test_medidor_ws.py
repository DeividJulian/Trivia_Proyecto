"""Pruebas de componente de la medición de WebSocket usada en las pruebas de carga."""

import pytest

from performance.medidor_ws import (
    CONEXION_FALLIDA,
    CONEXION_OK,
    LATENCIA,
    MENSAJE,
    MedidorDifusion,
    RegistroWS,
    leer_eventos,
    parsear_mensaje,
    percentil,
    por_escalon,
    resumir,
    url_websocket,
)

pytestmark = [pytest.mark.componente, pytest.mark.no_funcional]


@pytest.mark.parametrize(
    ("host", "esperado"),
    [
        ("http://127.0.0.1:8000", "ws://127.0.0.1:8000/ws/123456"),
        ("http://127.0.0.1:8000/", "ws://127.0.0.1:8000/ws/123456"),
        ("https://testquiz.onrender.com", "wss://testquiz.onrender.com/ws/123456"),
    ],
)
def test_url_websocket_cambia_el_esquema(host, esperado):
    assert url_websocket(host, "123456") == esperado


def test_url_websocket_rechaza_un_host_sin_esquema():
    with pytest.raises(ValueError, match="http"):
        url_websocket("127.0.0.1:8000", "123456")


@pytest.mark.parametrize("texto", ["no es json", "[1, 2]", '{"datos": {}}', b"\xff"])
def test_parsear_mensaje_descarta_lo_que_no_es_un_mensaje(texto):
    assert parsear_mensaje(texto) is None


def test_parsear_mensaje_acepta_el_formato_del_servidor():
    assert parsear_mensaje('{"tipo": "estado", "datos": {"estado": "LOBBY"}}')["tipo"] == "estado"


@pytest.mark.parametrize(("p", "esperado"), [(50, 3), (95, 5), (100, 5), (0, 1)])
def test_percentil_por_rango_mas_cercano(p, esperado):
    assert percentil([5, 1, 4, 2, 3], p) == esperado


def test_percentil_sin_valores_es_none():
    assert percentil([], 95) is None


def test_latencia_cuando_el_mensaje_llega_despues_del_200():
    medidor = MedidorDifusion()
    medidor.marcar_envio(10.000)

    assert medidor.confirmar(True) is None
    assert medidor.mensaje_recibido(10.025) == pytest.approx(25.0)


def test_latencia_cuando_el_mensaje_llega_antes_del_200():
    medidor = MedidorDifusion()
    medidor.marcar_envio(10.000)

    assert medidor.mensaje_recibido(10.012) is None
    assert medidor.confirmar(True) == pytest.approx(12.0)


def test_con_409_no_se_mide_latencia():
    """Un 409 no difunde nada: el siguiente mensaje es otro evento y no debe contar (sesgo corregido)."""
    medidor = MedidorDifusion()
    medidor.marcar_envio(10.0)

    assert medidor.confirmar(False) is None
    assert medidor.mensaje_recibido(13.0) is None


def test_solo_cuenta_el_primer_mensaje_tras_el_envio():
    medidor = MedidorDifusion()
    medidor.marcar_envio(1.0)
    medidor.confirmar(True)

    assert medidor.mensaje_recibido(1.010) == pytest.approx(10.0)
    assert medidor.mensaje_recibido(1.500) is None


def test_mensaje_sin_envio_no_genera_latencia():
    assert MedidorDifusion().mensaje_recibido(5.0) is None
    assert MedidorDifusion().confirmar(True) is None


def test_registro_rechaza_tipos_desconocidos():
    with pytest.raises(ValueError, match="desconocido"):
        RegistroWS().agregar(0.0, 10, "otro")


def test_registro_se_escribe_y_se_lee_igual(tmp_path):
    registro = RegistroWS()
    registro.agregar(0.5, 10, CONEXION_OK, 12.3456)
    registro.agregar(1.0, 10, MENSAJE)
    ruta = tmp_path / "prueba_ws_eventos.csv"

    registro.escribir(ruta)
    leidos = leer_eventos(ruta)

    assert [(e.usuarios, e.tipo) for e in leidos] == [(10, CONEXION_OK), (10, MENSAJE)]
    assert leidos[0].valor_ms == pytest.approx(12.346)


def test_resumir_cuenta_conexiones_mensajes_y_latencias():
    registro = RegistroWS()
    registro.agregar(0.0, 2, CONEXION_OK, 10)
    registro.agregar(0.0, 2, CONEXION_FALLIDA, 10)
    for momento in range(10):
        registro.agregar(float(momento), 2, MENSAJE)
    for latencia in (5, 10, 40):
        registro.agregar(1.0, 2, LATENCIA, latencia)

    resumen = resumir(registro.eventos, duracion_s=5.0)

    assert resumen["conexiones_ok"] == 1
    assert resumen["conexiones_fallidas"] == 1
    assert resumen["mensajes"] == 10
    assert resumen["mensajes_por_s"] == 2.0
    assert resumen["latencia_p50_ms"] == 10
    assert resumen["latencia_p95_ms"] == 40


def test_por_escalon_agrupa_por_usuarios_y_omite_cero():
    registro = RegistroWS()
    registro.agregar(0.0, 0, MENSAJE)
    registro.agregar(1.0, 50, MENSAJE)
    registro.agregar(3.0, 50, MENSAJE)
    registro.agregar(21.0, 100, LATENCIA, 30)

    filas = por_escalon(registro.eventos)

    assert [f["usuarios"] for f in filas] == [50, 100]
    assert filas[0]["mensajes"] == 2
    assert filas[0]["mensajes_por_s"] == 1.0
    assert filas[1]["latencia_p95_ms"] == 30
