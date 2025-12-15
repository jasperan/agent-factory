# Agent Factory - Production Dockerfile
# 24/7 Telegram Bot + Knowledge Base Automation
#
# Build: docker build -t agent-factory .
# Run: docker-compose up -d
# Health: curl http://localhost:9876/health

FROM python:3.10-slim

LABEL maintainer="Agent Factory Team"
LABEL description="24/7 Telegram Bot + Knowledge Base Automation System"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
# - git: Required for Poetry dependency resolution
# - curl: Required for health checks
# - ca-certificates: SSL/TLS support for API calls
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install Poetry and dependencies
# - Disable virtualenv creation (not needed in container)
# - Install production dependencies only (--no-dev)
# - No interaction mode for CI/CD compatibility
RUN pip install --no-cache-dir poetry==1.7.0 && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/logs data/cache data/extracted data/atoms data/reports

# Expose health check port
EXPOSE 9876

# Health check configuration
# - Checks every 30 seconds
# - 10 second timeout
# - 5 second startup grace period
# - Retry 3 times before marking unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9876/health || exit 1

# Environment variables with defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Run bot via module entry point
# Note: bot_manager.py is for LOCAL deployments with singleton lock
# Render/cloud deployments use module directly (one instance per service)
CMD ["poetry", "run", "python", "-m", "agent_factory.integrations.telegram"]
