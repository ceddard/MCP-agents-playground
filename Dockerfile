FROM python:3.11-slim

# set workdir
WORKDIR /usr/src/app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
 && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Use non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && chown -R appuser:appgroup /usr/src/app
USER appuser

ENV PYTHONUNBUFFERED=1
CMD ["/usr/local/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
