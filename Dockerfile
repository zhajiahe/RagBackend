FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY pyproject.toml uv.lock ./

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    pip install --no-cache-dir pip -U && \
    pip install --no-cache-dir hatch && \
    pip install --no-cache-dir '.[dev]' && \
    apt-get purge -y --auto-remove gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Expose the application port
EXPOSE 2024

# Command to run the application
CMD ["hatch", "run", "start"]