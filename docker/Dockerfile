# Surge — multi-stage build
FROM python:3.13-slim AS builder

WORKDIR /app

# System deps for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

FROM python:3.13-slim AS runtime

WORKDIR /app

# Non-root user
RUN useradd -m surge && mkdir -p /app/data && chown surge:surge /app/data

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/surge /usr/local/bin/surge
COPY --from=builder /app/src ./src
COPY pyproject.toml README.md ./
COPY docker/entrypoint.sh ./docker/entrypoint.sh

ENV PYTHONPATH=/app/src
ENV SURGE_DB_PATH=/app/data/surge.db

USER surge

RUN chmod +x ./docker/entrypoint.sh

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["surge"]
