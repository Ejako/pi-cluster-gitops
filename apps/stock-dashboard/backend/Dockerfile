# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install PostgreSQL client for wait script and curl for health checks
RUN apt-get update && \
    apt-get install -y postgresql-client curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Make sure this copies ALL .py files including config.py
COPY *.py .

USER appuser

EXPOSE 5000
CMD ["python", "app.py"]
