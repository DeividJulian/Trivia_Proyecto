# Guion de demo (3 minutos): el sabotaje cambia al ganador

Objetivo: mostrar en vivo que un defecto (el mutante `bono_sin_acierto`, el mismo error de la versión
v2 / DEF-011) **cambia quién gana**, que la ventana de daño lo hace visible y que las pruebas lo
detectan antes del despliegue.

Probado el 2026-11-06 contra uvicorn local con el reloj real: la partida se jugó por la API con los
tiempos de este guion (51 s de juego) y la ventana de daño se abrió en un navegador real (Playwright +
Chromium, 1280 × 720, sin errores de consola). Captura: [demo-ganador-cambiado.png](evidencias/demo-ganador-cambiado.png).

## Antes de la clase (preparación, 5 minutos)

En CMD, en la carpeta del proyecto:

```
cd "C:\Users\Jack Limas\Universidad\Trivia_Proyecto"
.venv\Scripts\activate
set ADMIN_TOKEN=demo123 && uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 75
```

Abrir en el navegador del proyector (cuatro pestañas):

| Pestaña | Dirección | Quién la usa |
|---|---|---|
| 1. Profesor | `http://127.0.0.1:8000/` → pestaña **Profesor** | Quien presenta |
| 2. Saboteador | `http://127.0.0.1:8000/` → pestaña **Saboteador**, token `demo123`, **Ver sabotajes** | Quien presenta |
| 3. Ventana de daño | `http://127.0.0.1:8000/dano.html`, token `demo123` | Se proyecta |
| 4. Jugadores | Tres pestañas o tres celulares en `http://127.0.0.1:8000/` → pestaña **Jugador** | Ana, Beto y Carla |

Los celulares solo funcionan si están en la misma red y el servidor escucha en `0.0.0.0`; con una
sola máquina, usar tres pestañas del mismo navegador.

## Los tres jugadores

Cada pregunta dura **20 s**. El bono por velocidad es 500 × (tiempo que sobra / 20 s).

| Jugador | Cómo juega | Qué representa |
|---|---|---|
| **Ana** | Responde **bien** la pregunta 1 y **mal** las preguntas 2 y 3. Siempre **lento**: cuando al reloj le quedan unos 3 s | Sabe, pero piensa |
| **Beto** | Responde **mal y rápido** las tres (en el primer segundo) | Adivina |
| **Carla** | Responde **mal** las tres a mitad de tiempo (unos 10 s) | Relleno |

## Minuto a minuto

| Tiempo | Acción | Qué decir |
|---|---|---|
| 0:00 | Profesor: **Crear partida**. Ana, Beto y Carla: PIN + nombre → **Entrar** | "Tres alumnos: Ana sabe, Beto adivina rápido." |
| 0:20 | Saboteador: activar **Bono sin acierto**. Proyectar la ventana de daño y elegir la partida | "Activamos un defecto real: es el error que tuvo la versión v2 (DEF-011)." |
| 0:30 | Profesor: **Iniciar**. Jugar las 3 preguntas como dice la tabla de arriba; tras cada una, **Siguiente** | "Miren cómo crecen las barras naranjas: lo que la pantalla muestra." |
| 1:30 | Señalar la ventana de daño | "Ganador real: Ana. Ganador mostrado: Beto. **El sabotaje cambió al ganador.** Beto no acertó ninguna y gana." |
| 2:00 | Saboteador: **Ejecutar pruebas** (con el sabotaje aún activo) | "Antes de desplegar, la suite lo detecta: el tablero marca qué módulos se caen y cuáles quedan en riesgo." |
| 2:40 | Saboteador: **Reparar todo** | "En el pipeline, este fallo bloquea el despliegue: no llega a producción." |

## Resultado esperado (medido el 2026-11-06)

| Jugador | Reales | Mostrados | Posición real | Posición mostrada |
|---|---|---|---|---|
| Ana | 1.075 | 1.223 | 1.º | 2.º |
| Beto | 0 | 1.425 | 2.º | **1.º** |
| Carla | 0 | 749 | 3.º | 3.º |

- Ventana de daño: **daño total 2.322** (suma en valor absoluto), **8 de 9 respuestas afectadas**,
  tile del ganador en rojo con "El sabotaje cambió al ganador".
- **Ejecutar pruebas** con `bono_sin_acierto` (mismo ejecutor del panel, 2026-11-06): 326 pruebas,
  **7 fallidas** (4 de componente, 1 de integración, 1 de sistema y 1 de aceptación); **Puntaje,
  Partida y API caídos**; Ranking y Gestor en riesgo. Unos 5 s.

Los números exactos varían unos pocos puntos según cuándo responda cada uno; lo que no cambia es
que Beto aparece primero sin haber acertado.

## Si algo falla en vivo

| Problema | Qué hacer |
|---|---|
| La ventana dice "Token de administrador incorrecto" | Revisar que el servidor se arrancó con `set ADMIN_TOKEN=demo123` |
| Ana termina ganando también en lo mostrado | Ana respondió muy rápido: el bono se lo dio a ella. Repetir con Ana respondiendo al final del tiempo |
| No aparece la partida en la ventana | Elegirla en la lista "Partida"; si se reinició el servidor, crear otra |
| "Ejecutar pruebas" responde 409 | Ya hay una ejecución en curso: esperar unos segundos |
