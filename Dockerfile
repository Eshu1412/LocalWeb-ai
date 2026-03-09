# ── LocalWeb AI — Python Backend Dockerfile ─────────────────
FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for QA Agent)
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home appuser
USER appuser

# Expose API port
EXPOSE 8000

# Default command (overridden by docker-compose)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
