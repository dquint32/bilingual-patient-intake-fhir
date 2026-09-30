# Use official Python image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Install runtime dependencies first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (tests and dev files are excluded by .dockerignore)
COPY backend/ /app/

# Run as an unprivileged user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080

# $PORT is injected by Railway/Render; Fly uses internal_port 8080.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
