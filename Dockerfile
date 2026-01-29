# Generated Dockerfile for python-code-sandbox-mcp

FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency definition and metadata
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .
COPY LICENSE .

# Install dependencies
# We use --no-install-project to install only the external dependencies first,
# which allows us to cache this layer even when source code changes.
ENV UV_SYSTEM_PYTHON=1
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install the project
COPY src/ src/
RUN uv sync --frozen --no-dev

# Set the python path to include src
ENV PYTHONPATH=/app/src

# Entrypoint
# We run the module. FastMCP's .run() handles the rest.
# The default transport is stdio.
ENTRYPOINT ["python", "-m", "python_code_sandbox_mcp.server"]
