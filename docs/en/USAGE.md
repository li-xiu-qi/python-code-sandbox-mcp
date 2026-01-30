# Usage Guide

## Quick Start: Using .env File (Recommended)

For easier local configuration, you can use a `.env` file:
1. Copy `.env.sample` to `.env` in the root directory.
2. Edit `.env` and fill in your host-side cache path.

### Complete Environment Variable Reference

| Environment Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `PIP_CACHE_PATH` | Recommended | None | Absolute path on your **HOST** machine for pip persistence. e.g., `/Users/me/.mcp-cache/pip`. |
| `ENABLE_PIP_CACHE` | No | `true` | Whether to enable pip caching. Makes subsequent installs near-instant. |
| `SANDBOX_MEMORY_LIMIT`| No | `2g` | Maximum memory limit per sandbox container (supports `m`, `g` units). |
| `SANDBOX_CPU_PERIOD` | No | `100000` | CPU period for CFS scheduler. Used with `SANDBOX_CPU_QUOTA`. |
| `SANDBOX_CPU_QUOTA` | No | `50000` | CPU quota limit. `50000/100000` = 0.5 cores. Set to `-1` for unlimited. |
| `SANDBOX_FILES_DIR` | No | None | Host path for persistent file storage. Files written to `./files/` in the container will be synced here. |
| `LOG_LEVEL` | No | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

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

### File Persistence to Host

To persist files beyond container lifetime, configure `SANDBOX_FILES_DIR`:

```bash
export SANDBOX_FILES_DIR="/home/user/sandbox-output"
```

Then write files to `./files/` in your code:

```python
plt.savefig('./files/chart.png')  # Saved to both container and host
```

See [PERSISTENCE.md](./PERSISTENCE.md) for detailed documentation.

### Note
By default, **NO** data is persistently saved to the host machine's hard drive. Once a container is destroyed, its data is unrecoverable.

## Docker Configuration

The server needs access to the host's Docker daemon to spawn sibling containers.

- **Mounting Docker Socket**: `-v /var/run/docker.sock:/var/run/docker.sock` is critical.
- **Images**: By default, it uses `python:3.11-slim`. You can specify others if needed, but ensure they have `python` and `pip`.

## Advanced Configuration

### Custom Docker Images

You can use custom Docker images by passing the `image` parameter. Requirements for custom images:

1. **Must have**: Python and pip installed and available in PATH
2. **Working directory**: Should be set to `/workspace` or similar
3. **Optional**: Pre-install heavy dependencies to speed up execution

Example Dockerfile for a custom image:

```dockerfile
FROM python:3.11-slim

# Install heavy dependencies
RUN pip install torch torchvision transformers

# Set working directory
WORKDIR /workspace

# Optional: Create non-root user for security
RUN useradd -m -u 1000 sandbox
USER sandbox
```

Build and use:
```bash
docker build -t my-custom-sandbox -f Dockerfile.custom .
```

Then in your request:
```json
{
  "image": "my-custom-sandbox",
  "code": "import torch; print(torch.__version__)"
}
```

### Concurrency and Multiple Sessions

The server supports multiple concurrent sandboxes:

```python
# Session 1: Data processing
container_1 = sandbox_initialize()  # ID: abc123
run_python(container_1, code="import pandas; df1 = ...")

# Session 2: Machine learning (simultaneous)
container_2 = sandbox_initialize()  # ID: def456
run_python(container_2, code="import torch; model = ...")

# Each session is completely isolated
```

**Considerations:**
- Each container consumes resources (memory, CPU)
- Total resource usage = sum of all active containers
- Background cleanup runs independently for all containers

### Execution Timeout

**Note**: Currently, there is no built-in execution timeout for individual code runs. Containers have a maximum lifetime of 1 hour (automatic cleanup), but individual code execution can run indefinitely.

**Workarounds:**

1. **Add timeout in your Python code:**
```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Execution exceeded time limit")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 seconds timeout
try:
    # Your code here
    pass
finally:
    signal.alarm(0)  # Cancel timeout
```

2. **Manual cleanup:** If code hangs, manually stop the container:
```bash
docker stop <container_id>
```

## Performance Optimization

### First Execution Slow?

First runs may be slow due to:
1. Docker image download
2. Initial pip cache population
3. Container startup overhead

**Optimization tips:**

1. **Pre-pull the base image:**
```bash
docker pull python:3.11-slim
```

2. **Enable pip caching:**
```bash
export PIP_CACHE_PATH="/home/user/.cache/pip"
```

3. **Use session mode** for multiple related tasks to avoid repeated container creation

4. **Use custom images** with pre-installed dependencies for heavy packages (PyTorch, TensorFlow, etc.)

### Resource Tuning

For memory-intensive tasks:
```bash
export SANDBOX_MEMORY_LIMIT=8g
export SANDBOX_CPU_QUOTA=200000  # 2 cores
```

For lightweight tasks (save resources):
```bash
export SANDBOX_MEMORY_LIMIT=512m
export SANDBOX_CPU_QUOTA=25000   # 0.25 cores
```

## Troubleshooting

- **"Docker is not running"**: Ensure Docker Desktop is started.
- **"Container not found"**: The container might have been cleaned up by the background scavenger (default timeout: 1 hour) or manually stopped.
- **"No space left on device"**: Clean up Docker volumes and images: `docker system prune -a`
- **"Memory limit too low"**: Increase `SANDBOX_MEMORY_LIMIT` or optimize your code to use less memory.
- **Network Issues**: Ensure containers have internet access to install pip packages.

For more troubleshooting tips, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

## Further Reading

- [API Reference](./API.md) - Complete tool documentation
- [Examples](./EXAMPLES.md) - Practical code examples
- [PERSISTENCE.md](./PERSISTENCE.md) - File persistence details
- [SECURITY.md](./SECURITY.md) - Security considerations
