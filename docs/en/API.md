# API Reference

Complete reference for all tools provided by the Python Code Sandbox MCP server.

## Overview

The server exposes the following tools:

| Tool | Mode | Description |
|------|------|-------------|
| `run_python_ephemeral` | Ephemeral | One-shot execution in a fresh container (recommended) |
| `sandbox_initialize` | Session | Start a persistent sandbox session |
| `run_python` | Session | Execute code in an existing session |
| `sandbox_exec` | Session | Execute shell commands in a sandbox |
| `sandbox_stop` | Session | Terminate and remove a sandbox |
| `search_pypi_packages` | Utility | Search for packages on PyPI |

---

## Ephemeral Mode Tools

### `run_python_ephemeral`

Execute Python code in a brand-new disposable container. This is the **recommended** approach for most use cases.

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | - | Python source code to execute |
| `dependencies` | `string[]` | No | `[]` | List of pip packages to install before execution |
| `image` | `string` | No | `python:3.11-slim` | Docker image to use for the container |

#### Returns

Array of content objects:

```typescript
[
  { type: "text", text: "..." },           // Console output (stdout/stderr)
  { type: "image", data: "...", mimeType: "image/png" },  // Generated images
  { type: "text", text: "..." }            // Other files (text or binary info)
]
```

#### Example

```json
{
  "code": "import matplotlib.pyplot as plt; plt.plot([1,2,3]); plt.savefig('./files/chart.png')",
  "dependencies": ["matplotlib"],
  "image": "python:3.11-slim"
}
```

#### Behavior

1. Creates a fresh container with the specified image
2. Installs dependencies (if specified)
3. Executes the Python code
4. Scans `/workspace` for generated files
5. Returns console output and files (images are returned as `image` type)
6. **Automatically destroys** the container

#### Error Handling

| Error | Description |
|-------|-------------|
| `Docker is not running` | Docker daemon is not accessible |
| `Failed to install dependencies` | Pip install failed (invalid package name, network issue) |
| `Execution failed` | Python code raised an exception |

#### Response Content Format

`run_python_ephemeral` returns `List[Content]`, where each element represents a type of content:

**1. Console Output (TextContent)**

Standard output (stdout) and standard error (stderr) from code execution:

```json
{
  "type": "text",
  "text": "--- STDOUT ---\nHello World\n--- STDERR ---\nWarning message\n"
}
```

**Format Details**:
- Content from `print()` appears in the `--- STDOUT ---` section
- Content from `print(..., file=sys.stderr)` or exception info appears in `--- STDERR ---`
- If a section has no output, its marker will not be displayed
- Unicode/UTF-8 content is fully supported

**2. Image Files (ImageContent)**

Returned when generating charts, supports `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`:

```json
{
  "type": "image",
  "data": "iVBORw0KGgoAAAANSUhEUgAAA...",
  "mimeType": "image/png"
}
```

**3. Text Files (TextContent)**

Text files created by code (.txt, .csv, .json, etc.):

```json
{
  "type": "text",
  "text": "--- File: data.csv ---\nid,name,value\n1,Alice,100\n2,Bob,200\n"
}
```

**4. Binary Files (TextContent)**

Binary files like PDF, Word, Excel (content cannot be embedded directly):

```json
{
  "type": "text",
  "text": "--- File: report.pdf (Binary content, 45678 bytes) ---\n"
}
```

**Note**: Binary files (like PDF) do not return actual content, only file size information. To get PDF content, use one of these methods:

**Method 1: Enable File Persistence** (Recommended)
Set `SANDBOX_FILES_DIR` environment variable, PDF will be saved to host directory:
```bash
export SANDBOX_FILES_DIR="/path/to/save/files"
```

**Method 2: Convert to base64 in Code**
Convert PDF to base64 and output to stdout in your code:
```python
import base64
with open('report.pdf', 'rb') as f:
    print(base64.b64encode(f.read()).decode())
```

**Complete Response Example**:

```json
[
  {
    "type": "text",
    "text": "--- STDOUT ---\nChart generated successfully\n"
  },
  {
    "type": "image",
    "data": "iVBORw0KGgoAAAANSUhEUgAAA...",
    "mimeType": "image/png"
  },
  {
    "type": "text",
    "text": "--- File: data.json ---\n{\"count\": 100, \"status\": \"ok\"}\n"
  }
]
```

---

## Session Mode Tools

Session mode allows you to maintain state across multiple executions.

### `sandbox_initialize`

Start a new persistent sandbox container.

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `image` | `string` | No | `python:3.11-slim` | Docker image to use |

#### Returns

`string`: Success message with container ID (e.g., `Sandbox initialized. Container ID: abc123def456`)

#### Example

```json
{
  "image": "python:3.11-slim"
}
```

#### Notes

- Container remains running until `sandbox_stop` is called or it times out (default: 1 hour)
- Container ID must be saved for subsequent calls

---

### `run_python`

Execute Python code in an existing sandbox session.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `container_id` | `string` | Yes | Container ID returned by `sandbox_initialize` |
| `code` | `string` | Yes | Python source code to execute |
| `dependencies` | `string[]` | No | Pip packages to install |

#### Returns

`string`: Execution results containing the following sections (in order):

1. **Dependency installation info** (if dependencies provided): `Installing dependencies: [...]`
2. **Execution marker**: `Executing Python code...`
3. **Execution result**: Contains `--- Execution Result ---`, stdout, and stderr

**Return Format Example**:

```
Installing dependencies: ['pandas', 'numpy']...
Dependencies installed.
Executing Python code...
--- Execution Result ---
STDOUT:
Hello World
42

STDERR:
```

#### Example

```json
{
  "container_id": "abc123def456",
  "code": "x = 42; print(x * 2)",
  "dependencies": ["numpy"]
}
```

#### Session Persistence

**Important Clarification**: Session mode persists the **container environment** and **filesystem state**, not Python variable memory state.

| What Persists | What Does NOT Persist |
|--------------|----------------------|
| [x] Installed packages | [ ] Python variables (new process each time) |
| [x] Created files | [ ] Memory state |
| [x] Files in working directory | [ ] Unsaved temporary data |

**Correct way to share state** (via files):

```python
# Call 1: Create data and save to file
{"container_id": "abc123", "code": "import pandas as pd; df = pd.DataFrame({'a': [1,2,3]}); df.to_csv('data.csv')"}

# Call 2: Read data from file
{"container_id": "abc123", "code": "import pandas as pd; df = pd.read_csv('data.csv'); print(df.shape)"}  # Output: (3, 1)
```

See [EXECUTION_MODES.md](./EXECUTION_MODES.md) for detailed differences between the two modes.

---

### `sandbox_exec`

Execute arbitrary shell commands in a sandbox.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `container_id` | `string` | Yes | Container ID |
| `command` | `string` | Yes | Shell command to execute |

#### Returns

`string`: Contains the following sections:

```
Exit Code: 0
STDOUT:
<stdard output content>

STDERR:
<standard error content>
```

**Notes**:
- `Exit Code: 0` indicates successful execution, non-zero indicates failure
- `STDOUT` section contains command's standard output
- `STDERR` section contains command's error output (empty if none)

#### Example

```json
{
  "container_id": "abc123def456",
  "command": "pip list"
}
```

#### Common Use Cases

- Check installed packages: `pip list`
- List files: `ls -la`
- Manual package installation: `pip install <package>`
- Check Python version: `python --version`

---

### `sandbox_stop`

Terminate and remove a sandbox container.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `container_id` | `string` | Yes | Container ID to stop |

#### Returns

`string`: Success or error message

#### Example

```json
{
  "container_id": "abc123def456"
}
```

#### Important

- All data in the container is **permanently deleted**
- Always call this when done with a session to free resources

---

## Utility Tools

### `search_pypi_packages`

Search for Python packages on PyPI.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | `string` | Yes | Search term (e.g., "pandas", "machine learning") |

#### Returns

`string`: List of matching packages with version and description (top 5 results)

#### Example

```json
{
  "query": "data visualization"
}
```

#### Response Format

```
- **matplotlib** (3.8.0): Comprehensive library for creating static, animated, and interactive visualizations
- **seaborn** (0.13.0): Statistical data visualization using matplotlib
- **plotly** (5.18.0): Interactive graphing library for Python
```

---

## Error Codes and Troubleshooting

### Common Errors

| Error Message | Cause | Solution |
|--------------|-------|----------|
| `Error: Docker is not running` | Docker daemon not started | Start Docker Desktop or Docker service |
| `Container not found` | Invalid container ID or container was cleaned up | Check container ID, create new session |
| `Failed to install dependencies` | Invalid package name, network issue, or dependency conflict | Verify package name with `search_pypi_packages` |
| `Execution failed` | Python code raised an exception | Check stderr for traceback |
| `No such file or directory` | Trying to access non-existent path | Verify file paths in your code |

### Resource Limits

Default limits applied to all containers:

| Resource | Default | Configurable |
|----------|---------|--------------|
| Memory | 2GB | `SANDBOX_MEMORY_LIMIT` env var |
| CPU | 0.5 cores | `SANDBOX_CPU_QUOTA` env var |
| Max lifetime | 1 hour | Not configurable (cleanup thread) |

---

## Best Practices

### When to use Ephemeral vs Session

**Use `run_python_ephemeral` when:**
- Running one-off scripts
- Generating plots or files
- No need to maintain state between calls
- Want automatic cleanup

**Use Session mode when:**
- Building up state across multiple steps
- Installing many dependencies (avoid repeated installs)
- Iterative development/debugging
- Long-running tasks that exceed a single execution

### Working with Files

**Ephemeral mode:**
```python
# Save to ./files/ to ensure it's captured
import matplotlib.pyplot as plt
plt.plot([1, 2, 3])
plt.savefig('./files/chart.png')  # Will be returned
plt.savefig('chart.png')          # May not be captured
```

**Session mode:**
```python
# Files persist for the session duration
with open('./files/data.txt', 'w') as f:
    f.write('persistent data')  # Available in subsequent calls
```

### Dependency Management

1. **Search first**: Use `search_pypi_packages` to verify exact package names
2. **Specify versions** (optional): `numpy==1.24.0`
3. **Enable caching**: Set `PIP_CACHE_PATH` for faster repeated installs

---

## Type Definitions

### Content Types

```typescript
interface TextContent {
  type: "text";
  text: string;
}

interface ImageContent {
  type: "image";
  data: string;        // Base64 encoded
  mimeType: string;    // e.g., "image/png", "image/jpeg"
}

interface EmbeddedResource {
  type: "resource";
  resource: {
    text: string;
    uri?: string;
  };
}
```
