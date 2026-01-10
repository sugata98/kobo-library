#!/bin/bash
set -e

# Get PORT from environment or default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT with 4 workers..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4
