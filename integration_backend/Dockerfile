# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Install system deps if needed (none required now)
# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code and run script
COPY app /app/app
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

# Expose port
EXPOSE 8000

# Add a healthcheck that pings the readiness endpoint
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=12 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:${APP_PORT:-8000}/ready || exit 1

# Default command to run the app via run.sh (loads .env if present and respects PORT/APP_PORT)
CMD ["/app/run.sh"]
