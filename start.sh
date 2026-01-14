#!/bin/sh
# Start script for Railway deployment
# Uses PORT env var set by Railway, defaults to 8000
exec uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
