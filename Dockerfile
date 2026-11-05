# Imagen de producción de TestQuiz – El Saboteador
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Usuario sin privilegios (uid 10001): el proceso nunca corre como root.
RUN groupadd --gid 10001 appuser \
 && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin appuser

COPY requirements.txt requirements-panel.txt ./
RUN pip install -r requirements-panel.txt

# El panel del Saboteador ejecuta pytest dentro del contenedor: se copian también las pruebas.
COPY pyproject.toml ./
COPY app ./app
COPY data ./data
COPY tests ./tests

USER 10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/salud', timeout=4)"

# 1 worker: el estado de las partidas vive en memoria (ver RESULTADOS_RENDIMIENTO.md).
# --timeout-keep-alive 75: evita los reinicios de conexión tras 5 s sin actividad (DEF-014).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips='*' --timeout-keep-alive 75"]
