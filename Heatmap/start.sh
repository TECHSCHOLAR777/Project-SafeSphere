#!/usr/bin/env bash
set -euo pipefail

# Start script for Heatmap FastAPI app inside container
PORT=${PORT:-8000}

echo "Starting Heatmap backend on 0.0.0.0:${PORT}"
export PYTHONPATH=/app
uvicorn Heatmap.backend_api:app --host 0.0.0.0 --port ${PORT} --workers 1
