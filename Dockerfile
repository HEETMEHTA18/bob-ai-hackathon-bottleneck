FROM python:3.12-slim

WORKDIR /app

# System deps — combined into one layer, cleaned up immediately
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js 20 in the same layer as system deps
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached layer — only rebuilds when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 5 -r requirements.txt

# Install frontend deps (cached layer — only rebuilds when package-lock.json changes)
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci --ignore-scripts

# Copy everything else
COPY . .

# Build frontend (outputs to frontend/dist — served by FastAPI in production)
RUN cd frontend && npm run build

EXPOSE 8000

# Shell form so ${PORT:-8000} is expanded at runtime — Railway injects $PORT
CMD sh -c "python3 -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
