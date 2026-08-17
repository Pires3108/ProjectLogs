FROM node:22-alpine AS mermaid
WORKDIR /assets
RUN npm install --ignore-scripts --no-audit --no-fund mermaid@11.16.1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
COPY --from=mermaid /assets/node_modules/mermaid/dist/mermaid.min.js ./app/static/vendor/mermaid.min.js
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
