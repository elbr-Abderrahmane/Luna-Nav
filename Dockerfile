# Multi-stage Full-Stack Dockerfile for LUNA NAV (Hugging Face Spaces / Render / Railway)
# Stage 1: Build React + TypeScript Frontend
FROM node:22-slim AS frontend-build
WORKDIR /workspace
COPY mock_data ./mock_data
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci
COPY frontend ./frontend
RUN cd frontend && VITE_API_URL="" npm run build

# Stage 2: Python 3.12 Backend + LOLA DEM + JPL DE421 Ephemeris + Static Frontend
FROM python:3.12-slim
WORKDIR /workspace/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY docs /workspace/docs
COPY mock_data /workspace/mock_data
COPY scripts /workspace/scripts
COPY backend /workspace/backend
COPY --from=frontend-build /workspace/frontend/dist /workspace/frontend/dist

# Pre-fetch NASA LOLA South Pole DEM (64 MB) and JPL DE421 ephemeris (17 MB) into /workspace/data
RUN mkdir -p /workspace/data/cache /workspace/data/raw && \
    python3 /workspace/scripts/fetch_data.py || true && \
    chmod -R 777 /workspace/data

ENV PYTHONPATH=/workspace/backend
ENV PORT=7860
EXPOSE 7860 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

