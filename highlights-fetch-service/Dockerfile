# Dockerfile for Render
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for downloaded database
RUN mkdir -p /tmp

# Use 4 workers for better concurrent request handling
# With streaming, memory usage per worker is reduced, allowing more workers
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4
