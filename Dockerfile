# ---------- Stage 1: Build Application Image ----------
FROM python:3.12-slim

# Set env vars
ENV POETRY_VERSION=2.1.1 \
    POETRY_HOME="/opt/poetry" \
    PATH="$POETRY_HOME/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Poetry and minimal build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        && curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get purge -y curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

# Install only main (non-dev) dependencies
RUN /opt/poetry/bin/poetry config virtualenvs.create false && \
    /opt/poetry/bin/poetry install --no-root --only main

# Copy application code
COPY api/ ./api/
COPY utils/ ./utils/

# Ensure any required directories are writable
RUN chown -R appuser:appuser /app

# Drop to non-root user
USER appuser

EXPOSE 8080

# Run the application
CMD ["/opt/poetry/bin/poetry", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"] 