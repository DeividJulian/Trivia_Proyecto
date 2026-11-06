"""Pruebas de componente del tablero de dominó y de la lectura del JUnit XML."""

import pytest

from app.calidad.ejecutor import CAIDO, EN_RIESGO, OK, ResultadoPrueba, armar_tablero, leer_junit

pytestmark = pytest.mark.componente


def prueba(nombre, modulos, fallo, nivel="componente"):
    return ResultadoPrueba(nombre=nombre, modulos=tuple(modulos), nivel=nivel, fallo=fallo)


def test_todo_ok_si_no_hay_fallos():
    tablero = armar_tablero([prueba("a", ["Puntaje"], False), prueba("b", ["API"], False)])

    assert {m: d["estado"] for m, d in tablero["modulos"].items()} == dict.fromkeys(tablero["modulos"], OK)
    assert tablero["resumen"]["fallidas"] == 0


def test_el_tablero_marca_caido_al_modulo_con_fallos_y_en_riesgo_a_sus_dependientes():
    tablero = armar_tablero(
        [
            prueba("test_racha", ["Puntaje"], True),
            prueba("test_ranking", ["Ranking"], False),
            prueba("test_api", ["API"], False),
            prueba("test_preguntas", ["Preguntas"], False),
        ]
    )
    estados = {m: d["estado"] for m, d in tablero["modulos"].items()}

    assert estados["Puntaje"] == CAIDO
    assert estados["Ranking"] == estados["Partida"] == estados["Gestor"] == estados["API"] == EN_RIESGO
    assert estados["Preguntas"] == OK
    assert tablero["modulos"]["Ranking"]["en_riesgo_por"] == ["Puntaje"]
    assert tablero["resumen"]["caidos"] == ["Puntaje"]


def test_un_modulo_caido_no_se_marca_en_riesgo():
    tablero = armar_tablero([prueba("p", ["Puntaje"], True), prueba("r", ["Ranking"], True)])

    assert tablero["modulos"]["Ranking"]["estado"] == CAIDO
    assert tablero["modulos"]["API"]["en_riesgo_por"] == ["Puntaje", "Ranking"]


def test_fallidas_por_nivel():
    tablero = armar_tablero(
        [
            prueba("a", ["API"], True, "sistema"),
            prueba("b", ["API"], True, "aceptacion"),
            prueba("c", ["API"], True, "sistema"),
        ]
    )

    assert tablero["resumen"]["por_nivel"] == {"sistema": 2, "aceptacion": 1}


def test_lee_modulos_nivel_y_fallos_del_junit(tmp_path):
    xml = tmp_path / "r.xml"
    xml.write_text(
        """<testsuites><testsuite>
        <testcase classname="tests.componente.test_puntaje" name="test_ok">
          <properties>
            <property name="modulo" value="puntaje"/><property name="nivel" value="componente"/>
          </properties>
        </testcase>
        <testcase classname="tests.sistema.test_api" name="test_falla">
          <properties>
            <property name="modulo" value="api"/><property name="nivel" value="sistema"/>
          </properties>
          <failure message="assert 1500 == 0">detalle</failure>
        </testcase>
        </testsuite></testsuites>""",
        encoding="utf-8",
    )

    resultados = leer_junit(xml)

    assert resultados[0] == ResultadoPrueba(
        "tests.componente.test_puntaje::test_ok", ("Puntaje",), "componente", False
    )
    assert resultados[1].fallo
    assert resultados[1].modulos == ("API",)
    assert resultados[1].mensaje == "assert 1500 == 0"
