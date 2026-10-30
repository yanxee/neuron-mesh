FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NEURON_DATA_DIR=/data \
    NEURON_HOST=0.0.0.0 \
    NEURON_PORT=8000

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY neuron_mesh ./neuron_mesh

RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 neuron \
    && mkdir -p /data \
    && chown -R neuron:neuron /data

USER neuron
EXPOSE 8000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"

CMD ["neuron-mesh", "serve"]

