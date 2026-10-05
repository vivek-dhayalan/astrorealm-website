# AstroRealm website + API. Build the place database first (python scripts/build_geonames.py),
# then:  docker build -t astrorealm .   and   docker run -p 8080:8080 --env-file .env astrorealm
FROM python:3.11-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements-swisseph.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt -r requirements-swisseph.txt

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MATCHAPI_ENGINE=swisseph \
    MATCHAPI_NOMINATIM=0 \
    MATCHAPI_GEO_DB=/app/data/geonames.sqlite
COPY --from=build /install /usr/local
WORKDIR /app
COPY LICENSE README.md ./
COPY app ./app
COPY data/geonames.sqlite ./data/geonames.sqlite
RUN useradd --system --uid 10001 web && chown -R web /app
USER web
# Cloud Run sends traffic to $PORT (8080 by default).
ENV PORT=8080 WORKERS=1
EXPOSE 8080
# --no-access-log: the app writes no request log of its own (form bodies are never logged anywhere).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS} --no-access-log"]
