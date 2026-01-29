# Contributing to Python Code Sandbox MCP

Thank you for your interest in contributing! This project aims to provide the best Python execution environment for MCP clients.

## Development Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/li-xiu-qi/python-code-sandbox-mcp.git
    cd python-code-sandbox-mcp
    ```

2.  **Install dependencies**:
    We use `uv` for dependency management.
    ```bash
    uv sync
    ```

3.  **Install pre-commit hooks**:
    ```bash
    uv run pre-commit install
    ```

4.  **Run tests**:
    ```bash
    uv run pytest tests/
    ```

## Code Style

We use `ruff` for linting and formatting. It is enforced via pre-commit and CI. You can run it manually:
```bash
uv run ruff check . --fix
uv run ruff format .
```

## Pull Request Process

1.  Ensure all tests pass.
2.  Update documentation if you add new features.
3.  Follow the [MIT License](LICENSE).
