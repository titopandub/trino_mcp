FROM python:3.10-slim

WORKDIR /app

# Create a non-root user
RUN groupadd -r trino && useradd --no-log-init -r -g trino trino && \
    mkdir -p /app/logs && \
    chown -R trino:trino /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install the MCP server
RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV TRINO_HOST=trino
ENV TRINO_PORT=8080
ENV TRINO_USER=trino
ENV TRINO_CATALOG=memory

# Expose ports for SSE transport and LLM API
EXPOSE 8000 8001

# Switch to non-root user
USER trino

# Health check - use port 8001 for the health check endpoint and LLM API
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command (can be overridden)
ENTRYPOINT ["python", "-m", "trino_mcp.server"]

# Default arguments (can be overridden)
CMD ["--transport", "sse", "--host", "0.0.0.0", "--port", "8000", "--trino-host", "trino", "--trino-port", "8080", "--debug"] 