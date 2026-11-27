# Dockerfile
# Build image for the web‑scraping pipeline
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Install dependencies (including build‑essential if needed)
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code (src/ and any config if present)
COPY src/ ./src/
COPY config/ ./config/  # optional – will be ignored if not present

# Set entrypoint to run the pipeline module
ENTRYPOINT ["python", "-m", "src.pipeline"]
