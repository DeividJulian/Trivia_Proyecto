"""Excepciones del dominio del juego."""


class ErrorPartida(Exception):  # noqa: N818 - nombre en español: "Error" va al inicio (DEF-006)
    """Error base: la acción no es válida en el estado actual de la partida."""


class PartidaNoEncontrada(ErrorPartida):
    """No existe una partida con el PIN indicado."""

    def __init__(self, pin: str) -> None:
        super().__init__(f"No existe una partida con el PIN {pin}.")
        self.pin = pin


class AccesoDenegado(ErrorPartida):
    """El token presentado no autoriza la acción solicitada."""

    def __init__(self, mensaje: str = "Token inválido: no tienes permiso para esta acción.") -> None:
        super().__init__(mensaje)
