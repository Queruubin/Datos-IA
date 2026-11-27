# Single-service image for the demo deployment (Render web service, Docker runtime).
# FastAPI serves the API under /api and the built React app at "/".
# The Gemini key is NOT baked in: set GEMINI_API_KEY as an environment variable of the service.

# --- 1. Build the frontend ---------------------------------------------------------------
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Empty API URL -> the app calls /api on its own origin (same service, no CORS).
ENV VITE_API_URL=""
RUN npm run build

# --- 2. Backend + data -------------------------------------------------------------------
FROM python:3.12-slim

# Hugging Face runs the container as UID 1000; everything it writes must belong to it.
RUN useradd --create-home --uid 1000 user
WORKDIR /app
COPY --chown=user backend/ backend/
COPY --chown=user curated_data/ curated_data/
COPY --from=frontend --chown=user /frontend/dist frontend/dist

WORKDIR /app/backend
RUN pip install --no-cache-dir -e .

USER user
# Build the analytics database at image build time: the curated package from the repo plus
# the open-data portal downloads. If the portal is down the build fails and can be retried.
RUN python -m app.cli ingest

ENV FRONTEND_DIST_DIR=/app/frontend/dist \
    CHAT_RATE_LIMIT_PER_MINUTE=10 \
    PYTHONUNBUFFERED=1

EXPOSE 7860
# The host platform (e.g. Render) injects PORT; 7860 is the local default.
# --proxy-headers: behind the platform's proxy, rate limiting must see each visitor's IP,
# not the proxy's (otherwise everyone shares one quota).
CMD exec uvicorn app.api.main:app --host 0.0.0.0 --port "${PORT:-7860}" \
    --proxy-headers --forwarded-allow-ips "*"
