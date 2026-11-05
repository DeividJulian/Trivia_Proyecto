"""Pruebas de componente del mapa de impacto."""

import pytest

from app.calidad.impacto import DEPENDIENTES, dependientes_directos, impacto_de, modulos_afectados

pytestmark = pytest.mark.componente


@pytest.mark.parametrize(
    ("modulo", "directos"),
    [
        ("Tiempo", {"Puntaje", "Racha"}),
        ("Racha", {"Puntaje"}),
        ("Puntaje", {"Ranking", "Partida"}),
        ("Preguntas", {"Partida", "Gestor"}),
        ("Partida", {"Ranking", "Gestor", "API"}),
        ("Ranking", {"API"}),
        ("API", set()),
    ],
)
def test_dependientes_directos_segun_la_matriz(modulo, directos):
    assert dependientes_directos(modulo) == directos


def test_cambio_en_tiempo_afecta_a_toda_la_cadena():
    assert modulos_afectados("Tiempo") == {"Racha", "Puntaje", "Ranking", "Partida", "Gestor", "API"}


def test_cambio_en_ranking_solo_afecta_a_la_api():
    assert modulos_afectados("Ranking") == {"API"}


def test_la_api_no_afecta_a_nadie():
    assert modulos_afectados("API") == frozenset()


def test_un_modulo_no_se_incluye_a_si_mismo():
    assert "Puntaje" not in modulos_afectados("Puntaje")


def test_impacto_de_varios_modulos_incluye_los_cambiados():
    assert impacto_de(["Ranking", "Gestor"]) == {"Ranking", "Gestor", "API"}


def test_modulo_desconocido_da_error_claro():
    with pytest.raises(ValueError, match="Módulo desconocido: 'Pagos'"):
        modulos_afectados("Pagos")


def test_el_mapa_no_tiene_dependientes_inexistentes():
    for dependientes in DEPENDIENTES.values():
        assert dependientes <= set(DEPENDIENTES)
