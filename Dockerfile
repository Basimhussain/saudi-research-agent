FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent ./agent
COPY memory ./memory
COPY schemas ./schemas
COPY tools ./tools
COPY main.py .

RUN groupadd --system agent && useradd --system --gid agent agent \
    && chown -R agent:agent /app
USER agent

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python main.py --healthcheck >/dev/null || exit 1

ENTRYPOINT ["python", "main.py"]
