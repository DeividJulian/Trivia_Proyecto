"""Pruebas de componente de la carga de bancos de preguntas."""

import json

import pytest

from app.dominio.preguntas import CATEGORIAS, cargar_preguntas

pytestmark = pytest.mark.componente

PREGUNTA_VALIDA = {"texto": "¿?", "opciones": ["A", "B", "C", "D"], "correcta": 2, "tiempo_limite": 10}


def test_carga_las_10_preguntas_de_pruebas_por_defecto():
    preguntas = cargar_preguntas()

    assert len(preguntas) == 10
    assert all(len(p.opciones) == 4 for p in preguntas)


def test_carga_las_12_preguntas_de_cultura_general():
    assert len(cargar_preguntas("cultura")) == 12


def test_categorias_disponibles():
    assert set(CATEGORIAS) == {"pruebas", "cultura"}


def test_categoria_inexistente_da_error_claro():
    with pytest.raises(ValueError, match="Categoría 'deportes' desconocida"):
        cargar_preguntas("deportes")


def test_carga_desde_una_ruta_explicita(tmp_path):
    ruta = tmp_path / "propias.json"
    ruta.write_text(json.dumps([PREGUNTA_VALIDA]), encoding="utf-8")

    preguntas = cargar_preguntas(ruta=ruta)

    assert preguntas[0].correcta == 2


def test_json_mal_formado_indica_el_archivo(tmp_path):
    ruta = tmp_path / "roto.json"
    ruta.write_text("[{ esto no es json", encoding="utf-8")

    with pytest.raises(ValueError, match="roto.json"):
        cargar_preguntas(ruta=ruta)


def test_json_que_no_es_lista(tmp_path):
    ruta = tmp_path / "objeto.json"
    ruta.write_text(json.dumps(PREGUNTA_VALIDA), encoding="utf-8")

    with pytest.raises(ValueError, match="lista de preguntas"):
        cargar_preguntas(ruta=ruta)


def test_pregunta_invalida_indica_su_numero(tmp_path):
    mala = {**PREGUNTA_VALIDA, "correcta": 7}
    ruta = tmp_path / "malas.json"
    ruta.write_text(json.dumps([PREGUNTA_VALIDA, mala]), encoding="utf-8")

    with pytest.raises(ValueError, match="Pregunta 2 de malas.json inválida"):
        cargar_preguntas(ruta=ruta)


def test_pregunta_sin_campo_obligatorio(tmp_path):
    ruta = tmp_path / "incompleta.json"
    ruta.write_text(json.dumps([{"texto": "¿?"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="Pregunta 1 de incompleta.json inválida"):
        cargar_preguntas(ruta=ruta)
