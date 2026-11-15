FROM python:3.12-slim

WORKDIR /workspace/backend

# Install system dependencies for rasterio / GDAL if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files (docs/explainers and mock_data are referenced by backend config)
COPY docs /workspace/docs
COPY mock_data /workspace/mock_data
COPY scripts /workspace/scripts
COPY backend /workspace/backend

ENV PYTHONPATH=/workspace/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

