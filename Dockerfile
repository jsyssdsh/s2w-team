# syntax=docker/dockerfile:1

# --- Stage 1: build the Next.js static export -------------------------------
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

# pnpm version is pinned in package.json's packageManager field; corepack reads it.
RUN corepack enable

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm build

# --- Stage 2: install backend deps and serve everything from FastAPI --------
FROM python:3.12-slim AS backend

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /usr/local/bin/

WORKDIR /app/backend

# Install dependencies first (no project code yet) so this layer stays cached
# across app-code changes -- schema.py / connection.py resolve db/schema.sql
# and the default db path via parents[3], so backend/ and db/ must keep the
# same sibling layout inside the image as they have in the repo.
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app
RUN uv sync --frozen --no-dev

COPY db/schema.sql db/seed.sql /app/db/

# Static export mounts at app/main.py's `Path(__file__).parent.parent / "static"`.
COPY --from=frontend-builder /app/frontend/out ./static

ENV S2W_DB_PATH=/app/db/s2w.db \
    PORT=8000 \
    PATH="/app/backend/.venv/bin:${PATH}"

EXPOSE 8000

# SQLite lives here so a container restart (same volume) keeps its data.
VOLUME ["/app/db"]

CMD ["/bin/sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
