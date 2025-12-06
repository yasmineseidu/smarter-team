FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration first (for caching)
COPY config/ ./config/

# Copy backend application
COPY app/backend/ ./app/backend/

# Install Python dependencies
WORKDIR /app/app/backend
RUN pip install --no-cache-dir -e .

WORKDIR /app

# Set Python path
ENV PYTHONPATH=/app:/app/app/backend

# Default command
CMD ["uvicorn", "app.backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
