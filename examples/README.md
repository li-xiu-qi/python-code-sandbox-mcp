#  Python Code Sandbox MCP - 

 Python MCP Client  Python Code Sandbox MCP Server 

##  

****

### 

- **Windows**: `%TEMP%/python-sandbox-mcp/files/`
- **macOS/Linux**: `/tmp/python-sandbox-mcp/files/`

### 

|  |  |  |
|------|-------------|------|
|  **** |  |  |
|  **** | `SANDBOX_FILES_DIR=/your/path` |  |
|  **** | `SANDBOX_FILES_DIR=""` | |

##  

### 1. Docker
 Docker 

```bash
#  Docker 
docker version
docker ps
```

**Windows **
-  Docker Desktop
- `$env:DOCKER_HOST="npipe:////./pipe/docker_engine"`

### 2. Python 

 Python 3.10 

### 3. 

```bash
#  examples 
cd examples

#  MCP 
pip install mcp

#  uv
uv pip install mcp
```

### 4. 

 `uv run`  MCP Server

```bash
# 
uv sync

# 
pip install -e .
```

##  

###  1

 MCP Server `utils.py`  `get_server_params`

```bash
# 
cd examples

# 
python 01_basic_print.py
```

###  2 Docker 

 Docker  `utils.py`

```python
# 
from utils import mcp_session, get_docker_server_params  # 

# 
server_params = get_docker_server_params(memory_limit="1g")
```



```bash
docker pull ghcr.io/li-xiu-qi/python-code-sandbox-mcp
```

##  

|  |  |  |  |
|------|------|------|-----------|
|  | `python 01_basic_print.py` |  |   |
|  | `python 02_with_dependencies.py` |  `requests`  HTTP  |   |
|  | `python 03_generate_image.py` |  matplotlib  |   |
|  | `python 04_read_write_files.py` |  |   |
|  | `python 05_session_based.py` |  |   |
| **** | `python 06_custom_files_dir.py` |  |   |
| **** | `python 07_no_persistence.py` |  |   |

##  

###  CPU 

 server 

```python
from utils import get_server_params

# : 1g , 0.5 CPU
server_params = get_server_params()

# : 2g , 1.0 CPU
server_params = get_server_params(memory_limit="2g", cpu_limit="1.0")
```

### 

```python
from utils import (
    get_server_params,                # 
    get_server_params_with_custom_dir, # 
    get_server_params_no_persistence   # 
)

# 1. 
server_params = get_server_params()

# 2. 
server_params = get_server_params_with_custom_dir("/my/custom/path")

# 3. 
server_params = get_server_params_no_persistence()
```

### Docker 

**Windows (PowerShell)**:
```powershell
$env:DOCKER_HOST="npipe:////./pipe/docker_engine"
python 01_basic_print.py
```

**Linux/Mac**:
```bash
export DOCKER_HOST=unix:///var/run/docker.sock
python 01_basic_print.py
```

### Claude Desktop

 `claude_desktop_config.json` 

```json
{
  "mcpServers": {
    "python-sandbox": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-e", "SANDBOX_MEMORY_LIMIT=1g",
        "-e", "SANDBOX_FILES_DIR=/host/path/to/files",
        "ghcr.io/li-xiu-qi/python-code-sandbox-mcp"
      ]
    }
  }
}
```

##  

###  1: "Docker is not running"

****:
```
Error: Docker is not running. Please start Docker Desktop.
```

****:
1.  Docker Desktop 
2. Windows :
   ```powershell
   $env:DOCKER_HOST="npipe:////./pipe/docker_engine"
   ```

###  2: "command not found: uv"

****:
```
'uv' 
```

****:
1.  uv: `pip install uv`
2.  `utils.py`  `python -m` 

###  3: 

****:  `Installing dependencies` 

****:
1. : `memory_limit="2g"`
2.  pip  `PIP_CACHE_PATH`
3. : `docker pull python:3.11-slim`

###  4: ModuleNotFoundError

****:
```
ModuleNotFoundError: No module named 'mcp'
```

****:
```bash
pip install mcp
```

###  5: 

****:
1.  `SANDBOX_FILES_DIR` 
2.  Docker 
3.  Server 

##  

### 

|  |  |  |  |
|--------|----------|--------|------|
| `run_python_ephemeral` | `code`, `dependencies?`, `image?` | `List[Content]` |  |
| `sandbox_initialize` | `image?` | `str` (container_id) |  |
| `run_python` | `container_id`, `code`, `dependencies?` | `str` |  |
| `sandbox_exec` | `container_id`, `command` | `str` |  shell  |

### 

`run_python_ephemeral`  `List[Union[TextContent, ImageContent, EmbeddedResource]]`:

- **TextContent**: 
- **ImageContent**: base64 
- **EmbeddedResource**: 

### 

 `/workspace`

```python
#  
with open('output.txt', 'w') as f:
    f.write('data')

# 
with open('/workspace/output.txt', 'w') as f:
    f.write('data')
```


1.  `/workspace` 
2. ****
3.  MCP 

##  



```python
#!/usr/bin/env python3
import asyncio
from utils import mcp_session, get_server_params, print_result

async def main():
    server_params = get_server_params(memory_limit="1g")
    
    code = '''
#  Python 
print("Hello!")

# 
with open('result.txt', 'w') as f:
    f.write("Result data")
'''
    
    dependencies = []  # 
    
    async with mcp_session(server_params) as session:
        result = await session.call_tool("run_python_ephemeral", {
            "code": code,
            "dependencies": dependencies,
            "image": "python:3.11-slim"
        })
        
        print_result(result)

if __name__ == "__main__":
    asyncio.run(main())
```

##  

- [ README](../README.md)
- [](../docs/USAGE.md)
- [](../docs/ARCHITECTURE.md)
- [](../docs/TROUBLESHOOTING.md)

---

**Happy Coding! **
