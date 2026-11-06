# Guía de despliegue en Render (para Deivid, dueño del repositorio)

Esta guía prepara el despliegue; **no despliega nada por sí sola**. Solo el dueño del repositorio
puede crear secretos y variables en GitHub. Ningún paso pide copiar un secreto en el chat, en un
commit ni en un documento.

## Qué ya está listo en el repositorio

| Pieza | Dónde | Qué hace |
|---|---|---|
| Blueprint | `render.yaml` | Servicio web `testquiz-el-saboteador`, `runtime: docker`, plan `free`, `healthCheckPath: /salud`, **`autoDeploy: false`**. `ADMIN_TOKEN` lo genera Render (`generateValue: true`); `PERMITIR_SABOTAJE=true`, `MAX_PARTIDAS=500`, `PARTIDA_TTL_MINUTOS=30` |
| Imagen | `Dockerfile` | `python:3.12-alpine` fijada por digest, usuario sin privilegios (uid 10001), sin pip, healthcheck a `/salud`, puerto `$PORT` |
| Identificador del despliegue | `GET /salud` → `"commit"` | Render define `RENDER_GIT_COMMIT` en cada despliegue; el humo lo compara con el SHA del pipeline |
| Job 7 – Reporte y despliegue | `.github/workflows/ci.yml` | Solo en `main`. Genera `REPORTE_PREDESPLIEGUE.md`; si **todas** las compuertas aprueban, exige `RENDER_DEPLOY_HOOK` y `APP_URL` y llama al Deploy Hook |
| Job 8 – Humo y release | `.github/workflows/ci.yml` | Espera hasta 15 min a que `$APP_URL/salud` responda el commit nuevo, corre `pytest -m integracion_sistemas` y **solo entonces** crea el GitHub Release `v1.0.<n>` con el reporte |

Como `autoDeploy` es `false`, Render **no** despliega al hacer push: solo cuando el pipeline aprueba
todas las compuertas y llama al Deploy Hook.

## Orden de los pasos (importante)

El servicio de Render tiene que estar ligado a la rama `main`: el humo exige que Render despliegue
**exactamente** el commit que probó el pipeline. Hoy `main` sigue en la fase 0 y no tiene
`render.yaml`, y el Deploy Hook solo existe después de crear el servicio. Por eso:

1. Integrar `develop` en `main` (cierre del proyecto, **solo con autorización del equipo**).
   El pipeline de ese push llegará hasta el job 7 y se detendrá en "Comprobar secreto de despliegue",
   porque todavía no existe `RENDER_DEPLOY_HOOK`. **Es lo esperado**: no despliega ni crea release.
2. Crear el servicio con el Blueprint (paso A).
3. Guardar `RENDER_DEPLOY_HOOK` y `APP_URL` en GitHub (pasos B y C).
4. Volver a ejecutar el pipeline de `main` (paso D).

## A. Crear el servicio con el Blueprint

1. Entrar a <https://dashboard.render.com> con la cuenta del equipo.
2. **New +** → **Blueprint**.
3. Conectar GitHub si lo pide y elegir el repositorio `DeividJulian/Trivia_Proyecto`.
4. Rama: **`main`**. Render lee `render.yaml` y muestra el servicio `testquiz-el-saboteador`.
5. **Apply**. Render construye la imagen con el `Dockerfile` y hace el primer despliegue
   (en el plan gratuito tarda varios minutos).
6. Cuando el estado diga **Live**, abrir el servicio y copiar su URL, por ejemplo
   `https://testquiz-el-saboteador.onrender.com` (la real puede llevar un sufijo).
7. Comprobar en el navegador: `https://<la-url>/salud` debe responder
   `{"estado":"ok","version":"1.0.0","commit":"<sha de main>"}`.

`ADMIN_TOKEN`: Render lo genera solo. Para la demo, verlo en el servicio → **Environment**.
No se copia a GitHub ni a ningún archivo.

## B. Secreto `RENDER_DEPLOY_HOOK`

1. En Render: servicio → **Settings** → sección **Deploy Hook** → copiar la URL.
   Es un secreto: cualquiera que la tenga puede desplegar.
2. En GitHub: repositorio → **Settings** → **Secrets and variables** → **Actions** →
   pestaña **Secrets** → **New repository secret**.
3. Name: `RENDER_DEPLOY_HOOK`. Secret: pegar la URL. **Add secret**.

## C. Variable `APP_URL`

1. Mismo lugar: **Secrets and variables** → **Actions** → pestaña **Variables** →
   **New repository variable**.
2. Name: `APP_URL`. Value: la URL del paso A.6, **sin barra al final**
   (`https://testquiz-el-saboteador.onrender.com`). **Add variable**.

`APP_URL` no es secreta (es la dirección pública), por eso va como variable y no como secreto.

## D. Volver a ejecutar el pipeline de `main`

1. GitHub → **Actions** → la ejecución de `main` que se detuvo en el job 7 → **Re-run all jobs**.
2. Resultado esperado:
   - Jobs 1 a 6 en verde (estilo, pruebas, Sonar, mutantes, Trivy, rendimiento).
   - Job 7: reporte **APTO PARA DESPLEGAR**, comprueba el secreto y la variable y llama al Deploy Hook.
   - Job 8: espera a que `/salud` responda el commit de `main`, corre el humo y crea el Release
     `v1.0.<n>` con `REPORTE_PREDESPLIEGUE.md` adjunto.
3. Anotar el despliegue en `docs/REGISTRO_DESPLIEGUES.md` (fecha, versión, commit, veredicto,
   enlace al pipeline y quién aprobó) con los datos reales de esa ejecución.

## Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Job 7 falla en "Comprobar secreto de despliegue" | Falta `RENDER_DEPLOY_HOOK` | Paso B |
| Job 7 falla en "Comprobar URL de la aplicación desplegada" | Falta `APP_URL` | Paso C |
| Job 7 da **NO DESPLEGAR** | Alguna compuerta falló | Abrir el artefacto `REPORTE_PREDESPLIEGUE` y corregir esa compuerta; no se despliega a mano |
| Job 8: "En 15 minutos el despliegue no respondió el commit…" | Render no terminó, falló el build o el servicio no está ligado a `main` | Ver los logs del servicio en Render; revisar que la rama sea `main` |
| La primera petición tarda casi un minuto | El plan gratuito duerme el servicio tras ~15 min sin tráfico | Es normal; el humo ya espera hasta 15 min |

## Qué no hacer

- No activar `autoDeploy`: el despliegue debe pasar por las compuertas.
- No desplegar con el botón **Manual Deploy** saltándose el pipeline.
- No pegar el Deploy Hook ni el `ADMIN_TOKEN` en commits, issues, capturas ni en el chat.
