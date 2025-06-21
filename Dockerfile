FROM python:3.11-slim

WORKDIR /app

# 设置国内镜像源
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list

# 配置pip国内源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# Copy requirements first for better layer caching
COPY pyproject.toml uv.lock ./

# Copy application code (needs to be done before pip install .[dev])
COPY . .

# Install build dependencies and runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libpq-dev && \
    pip install --no-cache-dir pip -U && \
    pip install --no-cache-dir hatch && \
    pip install --no-cache-dir '.[dev]' && \
    # Purge build-only dependencies
    apt-get purge -y --auto-remove gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Expose the application port
EXPOSE 8080

# Command to run the application
CMD ["uv", "run", "uvicorn", "ragbackend.server:APP", "--host", "0.0.0.0", "--port", "8080"]
