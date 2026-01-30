# Architecture

## Overview

**Python Code Sandbox MCP** adopts the **Orchestrator Pattern**. Unlike a traditional Jupyter Kernel Gateway, this server acts as a manager that provisions and orchestrates ephemeral, isolated execution environments on demand.

## Core Components

### 1. MCP Server (`src/python_code_sandbox_mcp/server.py`)
- Acts as the interface layer compliant with the Model Context Protocol (MCP).
- Exposes tools to clients (LLMs, IDEs).
- Manages request lifecycles but delegates actual execution to the backend.
- Contains a background **Scavenger Thread** to monitor and cleanup inactive containers, preventing resource leaks.

### 2. Docker Backend (`src/python_code_sandbox_mcp/docker_utils.py`)
- Interacts directly with the local Docker daemon using the `docker` Python SDK.
- Responsible for:
    - **Container Lifecycle**: `run`, `stop`, `remove`.
    - **Code Injection**: Safely injects Python code using Base64 encoding into the container, avoiding shell escaping issues.
    - **Dependency Management**: Dynamically handles `pip install` operations inside running containers.
    - **File I/O**: Reads files from the container workspace for retrieval.

## Data Flow

1.  **Request**: Client sends `run_python(code="print('hi')", container_id="...")`.
2.  **Validation**: Server checks if `container_id` exists in the active registry.
3.  **Execution**:
    - Code is Base64 encoded.
    - Sent to container via `docker exec`.
    - Python interpreter inside container decodes and executes.
4.  **Response**: Captures `stdout` and `stderr` and returns to client.

### Ephemeral Execution & File Retrieval (`run_python_ephemeral`)

To support one-off tasks and file generation (e.g., plotting), an ephemeral flow is introduced:
1.  **Start**: Provisions a new container.
2.  **Execute**: Installs dependencies and runs code.
3.  **Retrieve**: Scans `/workspace` for new files.
4.  **Read**: Reads file content using `cat` and Base64 encoding (distinguishing between text and binary/images).
5.  **Teardown**: Immediately destroys the container, regardless of success or failure.

## State Management

- **Persistence**: Filesystem changes within `/workspace` persist for the life of the container.
- **Session Scope**: A `container_id` defines a session. Once `sandbox_stop` is called or the container times out, all state is lost.
- **Concurrency**: The server uses a thread-safe dictionary (`active_sandboxes`) to track multiple concurrent sessions, allowing different users or agents to have their own isolated environments simultaneously.
