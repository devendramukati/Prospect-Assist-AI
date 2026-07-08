# Build context is the REPO ROOT (see render.yaml's dockerContext), not
# this directory, so this image can bake in a seeded demo dataset from the
# sibling synthetic-data-generator package at build time.

FROM python:3.11-slim

WORKDIR /app

COPY services/scoring-service/requirements.txt ./services/scoring-service/requirements.txt
RUN pip install --no-cache-dir -r services/scoring-service/requirements.txt

# Bake a seeded demo dataset into the image so the deployed service has data
# to serve immediately on first boot ("seed 200+ customers into the live
# deployment") — nothing generated here is ever real bank data, and
# rebuilding the image regenerates a fresh (but deterministic) dataset from
# the same seed. --output-dir is omitted so it lands at the same relative
# path (packages/synthetic-data-generator/data) that
# app/core/config.py's default SYNTHETIC_DATA_DIR already expects.
COPY packages/synthetic-data-generator ./packages/synthetic-data-generator
RUN pip install --no-cache-dir -r packages/synthetic-data-generator/requirements.txt \
    && python packages/synthetic-data-generator/cli.py --per-archetype 30 --seed prod-seed

COPY services/scoring-service/app ./services/scoring-service/app

WORKDIR /app/services/scoring-service

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
