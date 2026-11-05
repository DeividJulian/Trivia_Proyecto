"""Pruebas de componente del mapa de impacto."""

import pytest

from app.calidad.impacto import (
    DEPENDIENTES,
    dependientes_directos,
    impacto_de,
    modulos_afectados,
    planificar_regresion,
)

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


# --- Plan de regresión a partir de archivos ----------------------------------------------------


def test_cambio_en_puntaje_ejecuta_puntaje_y_sus_dependientes():
    plan = planificar_regresion(["app/dominio/puntaje.py"])

    assert plan.modulos_cambiados == {"Tiempo", "Racha", "Puntaje"}
    assert plan.argumentos_pytest() == ["-q", "-m", "api or gestor or partida or puntaje or ranking"]
    assert not plan.suite_completa


def test_cambio_en_ranking_solo_ejecuta_ranking_y_api():
    assert planificar_regresion(["app/dominio/ranking.py"]).argumentos_pytest() == [
        "-q",
        "-m",
        "api or ranking",
    ]


def test_cambio_en_el_banco_de_preguntas():
    plan = planificar_regresion(["data/cultura_general.json"])

    assert "preguntas" in plan.argumentos_pytest()[-1]


def test_rutas_de_windows_se_normalizan():
    assert planificar_regresion([r"app\api\rutas.py"]).argumentos_pytest() == ["-q", "-m", "api"]


def test_solo_documentacion_no_ejecuta_nada():
    plan = planificar_regresion(["docs/PLAN_DE_PRUEBAS.md", "README.md"])

    assert plan.argumentos_pytest() == []
    assert "documentación" in plan.motivo


def test_solo_pruebas_ejecuta_esas_pruebas():
    plan = planificar_regresion(["tests/componente/test_ranking.py"])

    assert plan.argumentos_pytest() == ["-q", "tests/componente/test_ranking.py"]


def test_archivo_desconocido_ejecuta_toda_la_suite():
    plan = planificar_regresion(["app/dominio/ranking.py", "requirements.txt"])

    assert plan.suite_completa
    assert plan.argumentos_pytest() == ["-q"]
    assert "requirements.txt" in plan.motivo
