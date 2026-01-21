# dARK Core Admin API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy orchestrator library (assumes it's available in build context)
# In production, this would be installed from a package registry
COPY dark-core-orchestrator /opt/dark-core-orchestrator
RUN pip install --no-cache-dir /opt/dark-core-orchestrator

# Copy application
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 dark && chown -R dark:dark /app
USER dark

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
