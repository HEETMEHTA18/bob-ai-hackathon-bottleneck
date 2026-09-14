FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 5 -r requirements.txt

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy everything
COPY . .

# Build frontend
RUN cd frontend && npm ci && npm run build

EXPOSE 8000

# Shell form so $PORT is expanded by the shell (Railway injects PORT at runtime)
CMD sh -c "python3 -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
