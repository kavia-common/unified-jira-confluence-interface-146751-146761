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

# Expose port 3001 (required by orchestrator/preview)
EXPOSE 3001

# Healthcheck: use Python stdlib to avoid missing wget/curl in slim images.
# Probes the readiness endpoint on configured port (default 3001).
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=12 \
  CMD python -c "import os,sys,http.client; \
p = int(os.environ.get('APP_PORT') or os.environ.get('PORT') or 3001); \
conn = http.client.HTTPConnection('127.0.0.1', p, timeout=3); \
conn.request('GET','/ready'); r=conn.getresponse(); sys.exit(0 if r.status==200 else 1)" || exit 1

# Default command to run the app via run.sh (loads .env if present and respects PORT/APP_PORT)
CMD ["/app/run.sh"]
