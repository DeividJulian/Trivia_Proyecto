"""Pruebas de componente de la comparación de escenarios de carga (REST vs. REST + WebSocket)."""

import pytest

from performance import comparar_escenarios as comparar
from performance.analizar_resultados import Escalon

pytestmark = [pytest.mark.componente, pytest.mark.no_funcional]

HISTORIAL = (
    "Timestamp,User Count,Type,Name,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%,"
    "Total Request Count,Total Failure Count\n"
    "1000,50,,Aggregated,40,0,5,6,7,8,9,10,11,12,13,14,15,100,0\n"
    "1010,50,,Aggregated,42,0,5,6,7,8,9,12,11,12,13,14,15,200,0\n"
    "1020,100,,Aggregated,80,0,5,6,7,8,9,30,11,12,13,14,15,400,0\n"
)
STATS = (
    "Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,Min Response Time,"
    "Max Response Time,Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,"
    "99.99%,100%\n"
    ",Aggregated,5000,0,4,5,1,90,100,42.0,0,4,5,5,6,7,9,12,15,40,90,90\n"
)


def _escalon(usuarios: int, p95: float) -> Escalon:
    return Escalon(usuarios=usuarios, peticiones=100, fallos_pct=0.0, p95_ms=p95, rps=40.0)


def _fila(usuarios: int, cpu_generador: float | None) -> comparar.FilaEscalon:
    cpu = {} if cpu_generador is None else {"generador_max": cpu_generador, "servidor_max": 50.0}
    return comparar.FilaEscalon(usuarios, _escalon(usuarios, 10), cpu, {})


@pytest.fixture
def resultados(tmp_path, monkeypatch):
    monkeypatch.setattr(comparar, "RESULTADOS", tmp_path)
    return tmp_path


def test_unir_escalones_junta_cpu_y_websocket_por_usuarios():
    filas = comparar.unir_escalones(
        [_escalon(50, 10), _escalon(100, 20)],
        {50: {"generador_max": 40.0, "servidor_max": 30.0}},
        [{"usuarios": 100, "mensajes_por_s": 300.0}],
    )

    assert filas[0].cpu["generador_max"] == 40.0 and filas[0].ws == {}
    assert filas[1].cpu == {} and filas[1].ws["mensajes_por_s"] == 300.0


def test_un_escalon_sin_datos_de_cpu_se_considera_fiable():
    assert _fila(50, None).fiable


@pytest.mark.parametrize(("cpu", "fiable"), [(89.9, True), (90.0, False), (100.0, False)])
def test_fiabilidad_en_el_limite_del_90_por_ciento(cpu, fiable):
    assert _fila(50, cpu).fiable is fiable


def test_conclusion_indica_desde_donde_no_son_fiables():
    filas = [_fila(50, 40.0), _fila(100, 80.0), _fila(150, 95.0), _fila(200, 70.0)]

    assert comparar.primer_no_fiable(filas) == 150
    assert comparar.conclusion_fiabilidad(filas) == (
        "Datos fiables hasta 100 usuarios; desde 150 usuarios Locust saturó su núcleo."
    )


def test_conclusion_sin_saturacion():
    assert "no saturó" in comparar.conclusion_fiabilidad([_fila(50, 40.0)])


def test_tabla_de_quiebre_desde_archivos_reales(resultados):
    (resultados / "q_stats_history.csv").write_text(HISTORIAL, encoding="utf-8")
    (resultados / "q_cpu.csv").write_text(
        "t,generador,servidor,sistema\n1005,50.0,20.0,30.0\n1025,95.0,60.0,70.0\n", encoding="utf-8"
    )
    (resultados / "q_ws_eventos.csv").write_text(
        "momento_s,usuarios,tipo,valor_ms\n1.0,50,mensaje,0\n3.0,50,mensaje,0\n2.0,50,latencia_difusion,25\n",
        encoding="utf-8",
    )

    filas = comparar.cargar_quiebre("q")
    tabla = comparar.tabla_quiebre("REST+WS · prueba", filas)

    assert [f.usuarios for f in filas] == [50, 100]
    assert filas[0].escalon.p95_ms == 12  # el mayor p95 del escalón
    assert "| 50 | 12 | 0.00 | 41 | 50 | 20 | 1 | 25 | sí |" in tabla
    assert "| 100 | 30 | 0.00 | 80 | 95 | 60 | — | — | **no** |" in tabla
    assert "desde 100 usuarios" in tabla


def test_tabla_de_carga_con_y_sin_websocket(resultados):
    for prefijo in ("rest", "ws"):
        (resultados / f"{prefijo}_stats.csv").write_text(STATS, encoding="utf-8")
    (resultados / "ws_ws_eventos.csv").write_text(
        "momento_s,usuarios,tipo,valor_ms\n0.5,50,conexion_ok,12\n1.0,50,mensaje,0\n2.0,50,latencia_difusion,8\n",
        encoding="utf-8",
    )

    tabla = comparar.tabla_carga(
        [("REST", comparar.fila_carga("rest")), ("REST+WS", comparar.fila_carga("ws"))]
    )

    assert "| REST | 5000 | 9 | 4 | 0.00 | 42.0 | — | — | — | — | — |" in tabla
    assert "| REST+WS | 5000 | 9 | 4 | 0.00 | 42.0 | — | — | 1 (0) | 1 (0) | 8 / 8 |" in tabla


def test_grafica_de_quiebre(resultados):
    pytest.importorskip("matplotlib")
    destino = resultados / "comparacion.png"

    comparar.graficar_quiebre([("REST", [_fila(50, 40.0), _fila(100, 95.0)])], destino)

    assert destino.stat().st_size > 0
