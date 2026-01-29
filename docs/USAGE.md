# Usage Guide

## Quick Start: Using .env File (Recommended)

For easier local configuration, you can use a `.env` file:
1. Copy `.env.sample` to `.env` in the root directory.
2. Edit `.env` and fill in your host-side cache path.

### Configuration Options

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `PIP_CACHE_PATH` | (Required) | Absolute path on your **HOST** machine for pip persistence. e.g., `/Users/me/.mcp-cache/pip`. |
| `ENABLE_PIP_CACHE` | `true` | Whether to enable pip caching. Makes subsequent installs near-instant. |
| `SANDBOX_MEMORY_LIMIT`| `2g` | Maximum memory limit per sandbox container (supports `m`, `g` units). |
| `SANDBOX_CPU_QUOTA` | `50000` | CPU quota limit. Combined with `CPU_PERIOD`(100000), `50000` means 0.5 cores. |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

## Tool Overview

### 1. `run_python_ephemeral` (Recommended for Quick Tasks)
Execute a script in a fresh container and get results immediately. Perfect for data analysis, plotting, or quick calculations.

**Example Prompt:**
> "Write a Python script to plot a sine wave and save it as 'sine.png'."

**How it works:**
1. Server starts a temporary container.
2. Installs `matplotlib` (if requested).
3. Runs the code.
4. Detects `sine.png` in the workspace.
5. Returns the image data and console output.
6. Deletes the container.

### 2. Session Mode (`sandbox_initialize` -> `run_python` -> `sandbox_stop`)
Use this when you need to maintain state (variables, defined functions) across multiple turns.

**Workflow:**
1. Call `sandbox_initialize()` -> Get `container_id`.
2. Call `run_python(container_id, code="x = 10")`.
3. Call `run_python(container_id, code="print(x + 5)")` -> Output: `15`.
4. Call `sandbox_stop(container_id)` when done.

### 3. `search_pypi_packages`
Find the exact name of a package before installing it.

**Example:**
> `search_pypi_packages(query="machine learning")`

## Execution Mechanism & Dependency Management

### 1. How is the code executed?
To ensure the code is transmitted safely and completely to the container, the server uses a **Base64 Encoding Injection** mechanism:
- The server converts your Python code into a Base64 string.
- It sends a command like `python -c "import base64; exec(...)"` via `docker exec`.
- This avoids shell parsing errors caused by special characters (quotes, newlines, escapes) in the code.

### 2. How are dependencies installed?
You have two ways to manage Python dependencies:
- **Automatic Installation (Recommended)**: Pass a list of package names in the `dependencies` parameter when calling `run_python` or `run_python_ephemeral`. The server will run `pip install` before executing your code.
- **Manual Installation**: Use the `sandbox_exec` tool to run the `pip install <package_name>` command directly.

#### Performance: Pip Caching
To speed up installations, you can enable persistent caching by setting the `PIP_CACHE_PATH` environment variable:
- Set it to an absolute path on your host machine (e.g., `/Users/yourname/.mcp/pip-cache`).
- Once enabled, repeated installations of the same packages will be nearly instantaneous.
- You can also set `ENABLE_PIP_CACHE=false` to completely disable caching.

*Note: All installations only persist for the duration of the container's lifecycle (unless a cache directory is used).*

## Data Persistence & Lifecycle

It is important to understand how data is handled in different modes:

### 1. Ephemeral Mode (`run_python_ephemeral`)
- **Use-and-Destroy**: Every call creates a **brand new** container.
- **Stateless**: Libraries installed or variables defined in previous calls are NOT preserved.
- **File Handling**: After execution, the server reads files from `/workspace` (e.g., generated images), returns them to the client, and then **immediately destroys** the container and all its data.

### 2. Session Mode (`sandbox_initialize`)
- **In-Session Persistence**: As long as `sandbox_stop` is not called, the container keeps running (until timeout).
- **State Preservation**: You can define a variable `x=1` in step 1, and `print(x)` in step 2.
- **File Staging**: You can generate files inside the container and read/modify them in subsequent steps.
- **Final Destruction**: When you call `sandbox_stop` or the container is idle for more than 1 hour (background cleanup), the container and its data are **permanently deleted**.

### ⚠️ Note
By default, **NO** data is persistently saved to the host machine's hard drive. Once a container is destroyed, its data is unrecoverable.

## Docker Configuration

The server needs access to the host's Docker daemon to spawn sibling containers.

- **Mounting Docker Socket**: `-v /var/run/docker.sock:/var/run/docker.sock` is critical.
- **Images**: By default, it uses `python:3.11-slim`. You can specify others if needed, but ensure they have `python` and `pip`.

## Troubleshooting

- **"Docker is not running"**: Ensure Docker Desktop is started.
- **"Container not found"**: The container might have been cleaned up by the background scavenger (default timeout: 1 hour) or manually stopped.
- **Network Issues**: Ensure containers have internet access to install pip packages.