# File Persistence Design

This document explains the file persistence design in the Python Code Sandbox MCP server.

## 1. Core Objective

To ensure that important data generated in sandbox containers (such as analysis charts, generated code files, or processed datasets) can be preserved on the host machine even after the container is destroyed.

## 2. Implementation

We use **Docker Bind Mounts** to persist files between the container and the host machine.

### Directory Mapping

| Location | Path | Description |
|----------|------|-------------|
| **Host** | Set via `SANDBOX_FILES_DIR` environment variable | User-specified directory on host machine |
| **Container** | `/workspace/files` | Fixed path inside the container |

### Automatic Mount Logic

1. When starting a sandbox, the system checks if `SANDBOX_FILES_DIR` is set.
2. If set, the system automatically creates the directory on the host if it doesn't exist.
3. The volume mount is added: `-v <host_path>:/workspace/files:rw`

## 3. Usage Guide

### Developer Configuration

Set the environment variable before starting the MCP server:

```bash
# Linux / macOS
export SANDBOX_FILES_DIR="/home/user/sandbox-output"

# Windows (PowerShell)
$env:SANDBOX_FILES_DIR = "C:\Users\YourName\Desktop\sandbox-output"

# Windows (CMD)
set SANDBOX_FILES_DIR=C:\Users\YourName\Desktop\sandbox-output
```

### For AI Models

The tool description instructs the model: **"If you need to persist files, write them to the `./files/` directory."**

Example Python code:

```python
import os

# Ensure directory exists (usually already mounted)
os.makedirs("files", exist_ok=True)

# Write persistent file
with open("files/report.txt", "w") as f:
    f.write("This content will persist after container destruction")

# Save charts
import matplotlib.pyplot as plt
plt.plot([1, 2, 3])
plt.savefig("./files/chart.png")
```

## 4. File Retrieval Mechanism

### Ephemeral Mode (`run_python_ephemeral`)

1. After script execution, the system recursively scans `/workspace` (max depth: 2).
2. Files in the `files/` directory are:
   - **Persisted** to the host machine (via bind mount)
   - **Returned** to the AI model as Base64 (images) or text
3. The system automatically filters out `__pycache__` and hidden files.

### Session Mode

1. Files written to `./files/` during the session are immediately synced to the host.
2. Files persist until the container is stopped or times out.
3. After `sandbox_stop`, files remain on the host but the container is deleted.

## 5. Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SANDBOX_FILES_DIR` | No | None | Host path for persistent file storage |

### Docker Compose Example

```yaml
version: '3.8'
services:
  mcp-sandbox:
    image: ghcr.io/li-xiu-qi/python-code-sandbox-mcp
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./sandbox-output:/workspace/files  # Persistent storage
    environment:
      - SANDBOX_FILES_DIR=/workspace/files
      - PIP_CACHE_PATH=/tmp/pip-cache
```

### Claude Desktop Config

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
        "-v", "/Users/me/sandbox-output:/workspace/files",
        "-e", "SANDBOX_FILES_DIR=/workspace/files",
        "ghcr.io/li-xiu-qi/python-code-sandbox-mcp"
      ]
    }
  }
}
```

## 6. Important Notes

**Warning: If `SANDBOX_FILES_DIR` is not configured:**
- `/workspace/files` exists only inside the container
- All data is lost when the container is destroyed
- No error is raised - files simply disappear

**Warning: Permission Requirements:**
- Ensure the host path has read/write permissions
- On Linux, the container runs as root by default

**Warning: Storage Limits:**
- Files persist indefinitely on the host until manually deleted
- Monitor disk usage for long-term usage

## 7. Comparison: Ephemeral vs Persistent

| Aspect | Without Persistence | With Persistence (`SANDBOX_FILES_DIR`) |
|--------|---------------------|----------------------------------------|
| Container lifespan | Temporary only | Temporary, but files survive |
| File access | Via tool return only | Host filesystem + tool return |
| Use case | One-off analysis | Batch processing, archiving results |
| Data volume | Limited by tool return size | Limited only by disk space |

### When to Disable Persistence

**Best for scenarios where printed output is sufficient:**

| Scenario | Example | Why It Fits |
|----------|---------|-------------|
| Text processing | Data analysis, log processing, text generation | Results are directly `print()` output, or written to text files and returned |
| Simple charts | Matplotlib line charts, bar charts | Returns `ImageContent`, LLM can view directly |
| Calculation validation | Algorithm testing, math calculations | Only need the stdout result |
| API calls | Web scraping, HTTP requests | Returns JSON/text data |

**Key characteristic**: The result is immediately visible in the response, no need to access files after the container is destroyed.

```python
# Example: Text analysis - suitable for disabled persistence
import pandas as pd
df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
print(df.describe())  # Direct output, done
```

**Important limitation**: Binary files (PDF, Word, Excel, etc.) cannot be retrieved if persistence is disabled. The tool only returns file size information, not content:

```
--- File: report.pdf (Binary content, 45678 bytes) ---
```

To access binary file content without persistence, you must encode it as base64 in your code and print it to stdout.

### When to Enable Persistence

**Best for scenarios requiring file retention:**

| Scenario | Example | Why It Fits |
|----------|---------|-------------|
| Binary document generation | PDF reports, Word documents, Excel spreadsheets | Files need to be accessed after container destruction |
| Batch image processing | Generating multiple charts, image pipelines | Results need to be reviewed or processed later |
| Intermediate artifacts | Model checkpoints, temporary datasets | Files are needed for subsequent processing steps |
| Long-term archiving | Analysis reports, generated code | Results need to be kept for future reference |

```python
# Example: Binary report generation - requires persistence
import pandas as pd
df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
df.to_excel('report.xlsx')  # Binary file, need persistence to access later
print("Report generated")
```

### Summary

- **Disable persistence**: "Compute and go" mode. Suitable for one-time tasks where results are immediately consumed via text output or images in the response.
- **Enable persistence**: "Workbench" mode. Suitable for tasks requiring retention of intermediate products, binary files, or post-hoc review.

## 8. Best Practices

### Do
- Always use `./files/` prefix for files you want to keep
- Organize files with subdirectories: `./files/reports/`, `./files/charts/`
- Clean up old files periodically to save disk space
- Use meaningful filenames with timestamps

```python
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"./files/report_{timestamp}.csv"
```

### Don't
- Write large files (>100MB) without checking disk space
- Store sensitive data without encryption
- Assume persistence is enabled without checking configuration
