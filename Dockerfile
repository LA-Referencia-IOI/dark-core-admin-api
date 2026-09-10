# dARK Core Admin API Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Build context is expected to be components so dark-core-lib is available.
# Example:
# docker build -f services/dark-core-admin-api/Dockerfile -t dark-core-admin-api .
COPY dark-core-admin-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy dark-core-lib from the sibling directory in the build context.
COPY dark-core-lib /opt/dark-core-lib
RUN pip install --no-cache-dir /opt/dark-core-lib

# Copy application
COPY dark-core-admin-api/app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 dark && chown -R dark:dark /app
USER dark

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
