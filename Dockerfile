# AstroRealm website + API. Build the place database first (python scripts/build_geonames.py),
# then:  docker build -t matchapi .   and   docker run -p 8000:8000 --env-file .env matchapi
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
EXPOSE 8000
# --no-access-log: request paths and IPs are not written to logs (form bodies never are).
# Proxy headers are trusted because the container only receives traffic through Cloudflare.
# One worker suits Cloudflare's "basic" instance (1/4 vCPU, 1 GiB); set WORKERS=2 on bigger machines.
ENV WORKERS=1
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS} --proxy-headers --forwarded-allow-ips '*' --no-access-log"]
