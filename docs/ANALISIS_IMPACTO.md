# Análisis de impacto

El análisis de impacto responde: **"si cambio este módulo, ¿qué más se puede romper?"**. Con la
respuesta se decide qué pruebas re-ejecutar (regresión) sin tener que probar siempre todo.

## Matriz de dependencias: módulo → módulos que dependen de él

| Si cambia… | …pueden fallar (dependientes directos) | Archivo |
|---|---|---|
| **Tiempo** (a tiempo, bono por velocidad) | Puntaje, Racha | `app/dominio/puntaje.py` |
| **Racha** | Puntaje | `app/dominio/puntaje.py` |
| **Puntaje** | Ranking, Partida | `app/dominio/puntaje.py` |
| **Preguntas** | Partida, Gestor | `app/dominio/preguntas.py`, `data/*.json` |
| **Partida** | Ranking, Gestor, API | `app/dominio/partida.py` |
| **Ranking** | API | `app/dominio/ranking.py` |
| **Gestor** | API | `app/dominio/gestor.py` |
| **API** | — (es la capa externa) | `app/api/`, `app/tiempo_real/`, `app/main.py`, `app/config.py` |

> Gestor no aparecía en la matriz inicial de la clase; se agregó porque crea las partidas con las
> preguntas y la API depende de él.

```
Tiempo ─┬─► Racha ─┐
        └──────────┴─► Puntaje ─┬─► Ranking ───────────► API
Preguntas ─┬──────────────────► Partida ─┬─► Ranking     ▲
           └─► Gestor ◄─────────────────┘   Gestor ─────┘
```

## Impacto transitivo

Un cambio se propaga: si cambia **Tiempo**, cambian Puntaje y Racha; si cambia Puntaje, cambian
Ranking y Partida; y así hasta la API. Por eso el efecto dominó de la Fase 9 (un cambio en el
bono por velocidad) rompió pruebas de componente, de sistema y de aceptación.

| Módulo cambiado | Afectados (transitivo) | Marcadores pytest a ejecutar |
|---|---|---|
| Tiempo | Racha, Puntaje, Ranking, Partida, Gestor, API | `puntaje or ranking or partida or gestor or api` |
| Puntaje | Ranking, Partida, Gestor, API | `puntaje or ranking or partida or gestor or api` |
| Ranking | API | `ranking or api` |
| Preguntas | Partida, Gestor, Ranking, API | `preguntas or partida or gestor or ranking or api` |
| API | — | `api` |

## Automatización

- `app/calidad/impacto.py` contiene el mapa y calcula los afectados de forma transitiva.
- `scripts/regresion_por_impacto.py` lee `git diff --name-only` contra `develop`, deduce los
  módulos cambiados y ejecuta `pytest -m` **solo** con los afectados.

```cmd
python scripts\regresion_por_impacto.py            REM ejecuta la regresión selectiva
python scripts\regresion_por_impacto.py --solo-ver REM muestra qué ejecutaría
```

Si cambia un archivo que no pertenece a ningún módulo (`pyproject.toml`, `requirements.txt`,
el CI…), el script ejecuta la suite completa: ante la duda, más pruebas.

## Regresión no significa probar todo

La regresión selectiva no reemplaza a la suite completa: la **adelanta**. El alcance depende de:

- **El riesgo:** un cambio en Puntaje (alto riesgo) arrastra casi todo; uno en la API, solo la API.
- **El tamaño del cambio:** un cambio de texto en un mensaje no exige lo mismo que una regla nueva.
- **El sistema:** con 180 pruebas que tardan 2 s se puede correr todo en el CI; la selección sirve
  para el ciclo rápido del desarrollador y para explicar el impacto. En sistemas grandes, donde la
  suite tarda horas, la selección es imprescindible.
