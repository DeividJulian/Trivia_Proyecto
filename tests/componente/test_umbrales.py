"""Pruebas de componente del verificador de umbrales de rendimiento (RNF-01 y RNF-02)."""

import pytest

from performance.verificar_umbrales import Resumen, evaluar, leer_agregado

pytestmark = [pytest.mark.componente, pytest.mark.no_funcional]

CABECERA = "Type,Name,Request Count,Failure Count,Median Response Time,Requests/s,95%\n"


def escribir(tmp_path, filas):
    ruta = tmp_path / "x_stats.csv"
    ruta.write_text(CABECERA + "".join(filas), encoding="utf-8")
    return ruta


def test_lee_la_fila_agregada(tmp_path):
    ruta = escribir(tmp_path, ["GET,/a,10,0,5,1.0,9\n", ",Aggregated,200,1,6,12.5,480\n"])

    assert leer_agregado(ruta) == Resumen(peticiones=200, fallos=1, p95_ms=480.0, mediana_ms=6.0, rps=12.5)


def test_sin_fila_agregada_da_error(tmp_path):
    with pytest.raises(ValueError, match="Aggregated"):
        leer_agregado(escribir(tmp_path, ["GET,/a,10,0,5,1.0,9\n"]))


@pytest.mark.parametrize(
    ("p95", "fallos", "cumple_p95", "cumple_fallos"),
    [
        (499.0, 0, True, True),
        (500.0, 0, False, True),  # valor límite: 500 ms ya NO cumple (p95 < 500)
        (100.0, 1, True, True),  # 1 de 1000 = 0,1 %
        (100.0, 10, True, False),  # 10 de 1000 = 1 %: valor límite, NO cumple (< 1 %)
    ],
)
def test_umbrales_con_valores_limite(p95, fallos, cumple_p95, cumple_fallos):
    resultados = evaluar(Resumen(peticiones=1000, fallos=fallos, p95_ms=p95, mediana_ms=1, rps=1))

    assert [cumple for *_, cumple in resultados] == [cumple_p95, cumple_fallos]
