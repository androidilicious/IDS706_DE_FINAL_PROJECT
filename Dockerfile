# Olist E-Commerce Data Pipeline
# Multi-stage Docker image for production deployment

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ingestion/ ./ingestion/
COPY transformation/ ./transformation/
COPY queries/ ./queries/
COPY tests/ ./tests/
COPY .env.example ./.env.example

# Create directories for outputs and logs
RUN mkdir -p /app/transformation/output /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Development stage
FROM base as development
RUN pip install --no-cache-dir pytest pytest-cov black flake8
CMD ["python", "ingestion/test_connections.py"]

# Production stage
FROM base as production
CMD ["python", "ingestion/ingestion_pipeline.py"]

# Test stage
FROM base as test
RUN pip install --no-cache-dir pytest pytest-cov
COPY tests/ ./tests/
CMD ["pytest", "tests/", "-v", "--cov=ingestion"]
