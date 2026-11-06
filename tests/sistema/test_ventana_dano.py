"""Pruebas de sistema de la ventana de daño del sabotaje (app/static/dano.html)."""

import re
from pathlib import Path

import pytest

from app.dominio import sabotajes
from tests.valores_prueba import TOKEN_ADMIN_PRUEBA

pytestmark = [pytest.mark.sistema, pytest.mark.api, pytest.mark.sabotajes]

ADMIN = {"X-Admin-Token": TOKEN_ADMIN_PRUEBA}
ESTATICOS = Path(__file__).resolve().parents[2] / "app" / "static"
JS = (ESTATICOS / "dano.js").read_text(encoding="utf-8")
HTML = (ESTATICOS / "dano.html").read_text(encoding="utf-8")

# Campos de la API que lee dano.js: si el backend los renombra, la ventana se rompería en silencio.
CAMPOS_JUGADOR = {
    "jugador",
    "puntos_reales",
    "puntos_mostrados",
    "diferencia",
    "posicion_real",
    "posicion_mostrada",
}
CAMPOS_RESPUESTA = {
    "numero_pregunta",
    "jugador",
    "correcta",
    "puntos_mostrados",
    "puntos_reales",
    "diferencia",
    "sabotajes_activos",
    "nota",
}


def test_la_ventana_se_sirve_con_cabeceras_de_seguridad(cliente):
    respuesta = cliente.get("/dano.html")

    assert respuesta.status_code == 200
    assert "text/html" in respuesta.headers["content-type"]
    assert "Ventana de daño del sabotaje" in respuesta.text
    assert respuesta.headers["X-Frame-Options"] == "DENY"
    assert respuesta.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize(("ruta", "tipo"), [("/dano.js", "javascript"), ("/dano.css", "text/css")])
def test_sirve_su_js_y_su_css(cliente, ruta, tipo):
    respuesta = cliente.get(ruta)

    assert respuesta.status_code == 200
    assert tipo in respuesta.headers["content-type"]


def test_no_carga_recursos_externos():
    referencias = re.findall(r'(?:src|href)="([^"]+)"', HTML)

    assert set(referencias) == {"dano.css", "dano.js"}
    assert "import " not in JS


@pytest.mark.seguridad
@pytest.mark.parametrize(
    "prohibido", ["innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("]
)
def test_no_inserta_html_con_datos(prohibido):
    assert prohibido not in JS


@pytest.mark.seguridad
@pytest.mark.parametrize("almacen", ["localStorage", "sessionStorage", "document.cookie", "indexedDB"])
def test_no_guarda_el_token_en_el_navegador(almacen):
    assert almacen not in JS


@pytest.mark.seguridad
def test_el_campo_del_token_no_se_autocompleta():
    campo = re.search(r'<input id="token"[^>]*>', HTML)

    assert campo is not None
    assert 'type="password"' in campo.group(0)
    assert 'autocomplete="off"' in campo.group(0)


def test_solo_usa_endpoints_existentes_del_panel(cliente):
    usados = set(re.findall(r'["`](/api/[^"`]+)["`]', JS))
    rutas = set(cliente.get("/openapi.json").json()["paths"])

    assert usados == {
        "/api/admin/sabotajes",
        "/api/admin/partidas",
        "/api/admin/partidas/${encodeURIComponent(pin)}/impacto",
    }
    assert {"/api/admin/sabotajes", "/api/admin/partidas", "/api/admin/partidas/{pin}/impacto"} <= rutas


def test_el_panel_enlaza_la_ventana_en_otra_pestana(cliente):
    enlace = re.search(r'<a id="adm-enlace-dano"[^>]*>', cliente.get("/").text)

    assert enlace is not None
    assert 'href="/dano.html"' in enlace.group(0)
    assert 'target="_blank"' in enlace.group(0)
    assert "noopener" in enlace.group(0)


def test_la_api_entrega_los_campos_que_lee_la_ventana(cliente, partida_creada, reloj):
    """Contrato: partida con racha_no_suma y bono_sin_acierto activos, como en la demo."""
    sabotajes.activar("racha_no_suma")
    sabotajes.activar("bono_sin_acierto")
    pin, token = partida_creada["pin"], partida_creada["token_host"]
    host = {"X-Host-Token": token}
    for nombre in ("Ana", "Beto"):
        cliente.post(f"/api/partidas/{pin}/jugadores", json={"nombre": nombre})
    cliente.post(f"/api/partidas/{pin}/iniciar", headers=host)
    for numero in range(2):  # la correcta de la pregunta i es la opción i
        reloj.avanzar(1.0)
        cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Ana", "opcion": numero})
        cliente.post(f"/api/partidas/{pin}/respuestas", json={"nombre": "Beto", "opcion": 3})
        cliente.post(f"/api/partidas/{pin}/siguiente", headers=host)

    impacto = cliente.get(f"/api/admin/partidas/{pin}/impacto", headers=ADMIN).json()
    catalogo = cliente.get("/api/admin/sabotajes", headers=ADMIN).json()["catalogo"]

    assert {"sabotajes_activos", "jugadores", "respuestas", "resumen_por_sabotaje"} <= impacto.keys()
    assert set(impacto["sabotajes_activos"]) == {"racha_no_suma", "bono_sin_acierto"}
    assert all(j.keys() >= CAMPOS_JUGADOR for j in impacto["jugadores"])
    assert all(r.keys() >= CAMPOS_RESPUESTA for r in impacto["respuestas"])
    resumen = impacto["resumen_por_sabotaje"].values()
    assert all(d.keys() >= {"respuestas_afectadas", "puntos_de_diferencia"} for d in resumen)
    assert all(s.keys() >= {"clave", "nombre"} for s in catalogo)
    beto = next(j for j in impacto["jugadores"] if j["jugador"] == "Beto")
    ana = next(j for j in impacto["jugadores"] if j["jugador"] == "Ana")
    assert beto["diferencia"] > 0  # recibió bono sin acertar
    assert ana["diferencia"] < 0  # su racha no sumó


def test_las_tablas_se_desplazan_dentro_de_su_panel():
    """DEF-035: en pantallas angostas las tablas no deben empujar la página a lo ancho."""
    for cuerpo in ("tabla-posiciones", "tabla-respuestas"):
        inicio = HTML.index(f'id="{cuerpo}"')
        contenedor = HTML.rfind('<div class="tabla-desplazable">', 0, inicio)
        cierre = HTML.rfind("</div>", 0, inicio)
        assert contenedor > cierre, f"{cuerpo} no está dentro de .tabla-desplazable"


def test_el_dano_total_aclara_que_suma_en_valor_absoluto():
    """Daño total suma |diferencia|: −300 y +422 cuentan 722, no 122."""
    assert "valor absoluto" in HTML
    assert "Math.abs(r.diferencia)" in JS
