# Python Code Sandbox MCP Server

[![Chinese](https://img.shields.io/badge/lang--red.svg)](README_ZH.md)

Python server implementing the Model Context Protocol (MCP) for running arbitrary Python in ephemeral Docker containers with on‑the‑fly pip dependency installation.

## Features

- **File Persistence** (Smart Default): Files are automatically persisted to the host filesystem by default.
- **Isolated Execution**: Runs Python code in ephemeral Docker containers (`python:3.11-slim` by default).
- **One-Shot Execution**: Run scripts in a disposable container and retrieve results instantly.
- **Session-Based Execution**: Keep a container alive for complex, multi-step tasks.
- **Dependency Management**: Automatically installs pip packages from PyPI.
- **Security First**: Controlled CPU/Memory limits and non-root execution inside containers.
- **File Retrieval**: Automatically captures generated images (plots) and files.

## Prerequisites

Docker must be installed and running on your machine.

**Tip:** Pre-pull the base image to avoid delays during first execution:
```bash
docker pull python:3.11-slim
```

## Getting Started

### Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "python-sandbox": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-e", "SANDBOX_MEMORY_LIMIT=1g",
        "-e", "SANDBOX_CPU_LIMIT=0.5",
        "ghcr.io/li-xiu-qi/python-code-sandbox-mcp"
      ]
    }
  }
}
```

### Manual Execution (Docker)

```bash
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e SANDBOX_MEMORY_LIMIT=1g \
  ghcr.io/li-xiu-qi/python-code-sandbox-mcp stdio
```

## Configuration

The server supports configuration via environment variables or a `.env` file. Key options include:

### File Persistence (New)

By default, files created in the sandbox are persisted to the host filesystem:

- **Windows**: `%TEMP%/python-sandbox-mcp/files/`
- **macOS/Linux**: `/tmp/python-sandbox-mcp/files/`

You can customize this behavior:

- `SANDBOX_FILES_DIR`: Set a custom directory for file persistence (e.g., `/home/user/my-sandbox-files`)
- `SANDBOX_FILES_DIR=""`: Set to empty string to disable persistence (files exist only in container)

### Other Options

- `PIP_CACHE_PATH`: (Recommended) Absolute path on your host for persistent pip caching.
- `SANDBOX_MEMORY_LIMIT`: Maximum memory per container (default: `2g`).
- `SANDBOX_CPU_LIMIT`: CPU limit per container (default: `0.5`).
- `ENABLE_PIP_CACHE`: Set to `false` to disable caching.

See the [Usage Guide](docs/en/USAGE.md) for a full list of variables.

## Tools

### `run_python_ephemeral` (Recommended)
Run a one-off Python script in a brand-new disposable container.

**Inputs:**
- `code` (string, required): Python source to execute.
- `dependencies` (array of strings, optional): Pip packages to install (e.g., `["pandas", "matplotlib"]`).

**Behavior:**
1. Creates a fresh container.
2. Installs specified dependencies.
3. Executes the script and captures stdout/stderr.
4. Returns generated files (images as `image`, others as `resource`).
5. Tears down the container automatically.

### `sandbox_initialize` / `run_python`
Start a persistent sandbox and run multiple scripts in the same environment.

## Test Prompts

Once connected, try these prompts to verify:

1. **Hello World**: `Create and run a Python script with print("Hello MCP")`
2. **Data Visualization**: `Install matplotlib and create a sine wave plot saved as 'sine.png'`

## Documentation

- [Usage Guide](docs/en/USAGE.md) - Installation, configuration, and usage
- [API Reference](docs/en/API.md) - Complete tool documentation
- [Execution Modes](docs/en/EXECUTION_MODES.md) - Ephemeral vs Session mode explained
- [Examples](examples/README.md) - Practical code examples with MCP client
- [Persistence](docs/en/PERSISTENCE.md) - File persistence and storage options
- [Architecture](docs/en/ARCHITECTURE.md) - System design
- [Security](docs/en/SECURITY.md) - Security guidelines
- [Troubleshooting](docs/en/TROUBLESHOOTING.md) - Common issues and solutions

### Chinese Documentation

- [使用指南](docs/zh/USAGE.md) - 安装、配置和使用说明
- [API 参考](docs/zh/API.md) - 完整工具文档
- [执行模式](docs/zh/EXECUTION_MODES.md) - 临时模式与会话模式详解
- [使用示例](docs/zh/EXAMPLES.md) - 实用代码示例

## License
MIT
