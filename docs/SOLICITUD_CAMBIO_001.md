# Solicitud de cambio 001 – Bono por velocidad

| Campo | Valor |
|---|---|
| Solicitante | Profesor (cliente) |
| Fecha | 2026-11-04 |
| Versión base | `v1-sin-bono` |
| Tipo de mantenimiento | **Evolutivo** (nueva funcionalidad pedida por el cliente) |
| Prioridad | Alta (se mostrará en la exposición) |

## Descripción

> "Quiero dar puntos extra a quien responda más rápido."

**Regla nueva:** una respuesta **correcta y a tiempo** suma, además de los 1000 puntos base y del
bono de racha, un **bono por velocidad de hasta 500 puntos, proporcional al tiempo que le sobró**:

```
bono = round(500 × (tiempo_límite − tiempo_respuesta) / tiempo_límite)
```

| Tiempo de respuesta (límite 20 s) | Bono |
|---|---|
| 0 s (inmediata) | 500 |
| 10 s (mitad del tiempo) | 250 |
| 20 s (justo en el límite) | 0 |
| Respuesta incorrecta o tarde | 0 (y la respuesta vale 0 en total) |

## Análisis de impacto

Antes de tocar el código se revisa **qué depende de qué** (matriz completa en la Fase 10):

```
Tiempo ──► Puntaje ──► Ranking ──► API
             │  ▲          ▲
             │  └─ Racha    │
             └──► Partida ──┘
```

| Módulo | ¿Cambia? | Riesgo | Pruebas a re-ejecutar |
|---|---|---|---|
| **Puntaje** (`puntaje.py`) | Sí: nueva función `calcular_bono_velocidad` y cambio en `calcular_puntos` | **Alto**: es donde vive la regla | `-m puntaje` (componente) |
| **Racha** (dentro de puntaje) | No debería | Medio: `calcular_puntos` también decide la racha; un cambio mal hecho puede romperla | `-m puntaje` |
| **Ranking** (`ranking.py`) | No | Medio: más puntos cambian el orden; los desempates por tiempo pierden peso | `-m ranking` |
| **Partida** (`partida.py`) | No | Medio: acumula los puntos que devuelve `calcular_puntos` | `-m partida` (integración) |
| **API** (`api/`) | No | Medio: expone puntos y ranking | `-m api` (sistema) y aceptación |
| Preguntas, Gestor, Config | No | Bajo | Suite completa al final |

**Regresión planificada:** primero la prueba nueva y la que falle (re-ejecución), luego
`pytest -m "puntaje or ranking or partida or api"` (regresión selectiva por impacto) y por último
la suite completa.

## Criterios de aceptación del cambio

1. Correcta e inmediata → 1000 + 500. Correcta a mitad de tiempo → 1000 + 250.
2. Correcta justo en el límite → 1000 (bono 0). Tarde → 0.
3. **Incorrecta → 0, sin importar lo rápida que sea.**
4. La racha y su bono funcionan igual que en v1.
5. Todas las pruebas que ya existían siguen pasando.
