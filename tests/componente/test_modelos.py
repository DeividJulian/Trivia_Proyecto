"""Pruebas de componente de la validación del modelo Pregunta."""

import pytest

from app.dominio.modelos import EstadoPartida, Jugador, Pregunta

pytestmark = pytest.mark.componente

OPCIONES = ("A", "B", "C", "D")


def test_pregunta_valida_conserva_sus_datos():
    pregunta = Pregunta(texto="¿2 + 2?", opciones=["3", "4", "5", "6"], correcta=1, tiempo_limite=10)

    assert pregunta.opciones == ("3", "4", "5", "6")
    assert pregunta.correcta == 1
    assert pregunta.tiempo_limite == 10


@pytest.mark.parametrize("opciones", [("A", "B", "C"), ("A", "B", "C", "D", "E"), ()])
def test_pregunta_exige_exactamente_cuatro_opciones(opciones):
    with pytest.raises(ValueError, match="exactamente 4 opciones"):
        Pregunta(texto="¿?", opciones=opciones, correcta=0)


def test_pregunta_no_admite_opciones_vacias():
    with pytest.raises(ValueError, match="vacía"):
        Pregunta(texto="¿?", opciones=("A", " ", "C", "D"), correcta=0)


@pytest.mark.parametrize("indice", [-1, 4])
def test_indice_correcto_fuera_de_rango(indice):
    with pytest.raises(ValueError, match="entre 0 y 3"):
        Pregunta(texto="¿?", opciones=OPCIONES, correcta=indice)


@pytest.mark.parametrize("indice", [0, 3])
def test_indices_en_los_limites_son_validos(indice):
    assert Pregunta(texto="¿?", opciones=OPCIONES, correcta=indice).correcta == indice


def test_pregunta_sin_texto():
    with pytest.raises(ValueError, match="texto"):
        Pregunta(texto="   ", opciones=OPCIONES, correcta=0)


@pytest.mark.parametrize("tiempo", [0, -5])
def test_tiempo_limite_debe_ser_positivo(tiempo):
    with pytest.raises(ValueError, match="tiempo límite"):
        Pregunta(texto="¿?", opciones=OPCIONES, correcta=0, tiempo_limite=tiempo)


def test_jugador_empieza_en_cero():
    jugador = Jugador(nombre="Ana")

    assert (jugador.puntos, jugador.racha, jugador.tiempo_total) == (0, 0, 0.0)


def test_estados_de_la_partida():
    assert [estado.value for estado in EstadoPartida] == ["LOBBY", "PREGUNTA", "RESULTADOS", "FINALIZADA"]
