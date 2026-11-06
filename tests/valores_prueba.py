"""Valores compartidos por las pruebas.

Los tokens se definen una sola vez aquí para no repetir literales con aspecto de credencial
en cada prueba (ver DEF-004 y DEF-005): son valores inventados, no secretos reales.
"""

TOKEN_ADMIN_PRUEBA = "token-admin-de-prueba"  # noqa: S105 - valor de prueba, no es una credencial (DEF-005)
OTRO_TOKEN_PRUEBA = "otro-token-de-prueba"  # noqa: S105 - valor de prueba, no es una credencial (DEF-005)
