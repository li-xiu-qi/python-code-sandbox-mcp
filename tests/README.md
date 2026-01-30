#  Python Code Sandbox MCP - 测试文档

本目录包含 Python Code Sandbox MCP Server 的单元测试和集成测试。

##  测试文件结构

```
tests/
├── README.md              # 本文件
├── test_config.py         # 配置和环境变量测试 (5 个测试)
├── test_docker_utils.py   # Docker 工具函数测试 (14 个测试)
└── test_server.py         # MCP Server 接口测试 (2 个测试)
```

总计：**21 个测试**

##  运行测试

### 运行所有测试

```bash
# 在项目根目录
python -m pytest tests/ -v
```

### 运行特定测试文件

```bash
python -m pytest tests/test_config.py -v
python -m pytest tests/test_docker_utils.py -v
python -m pytest tests/test_server.py -v
```

---

##  测试详解

### 1. test_config.py - 配置和环境变量测试

测试环境变量的读取、默认值处理，以及文件持久化配置。

#### `test_config_loading_from_env`

| 项目 | 说明 |
|------|------|
| **目的** | 验证程序能正确从环境变量读取配置 |
| **输入** | 环境变量：`PIP_CACHE_PATH=/tmp/fake-cache`, `ENABLE_PIP_CACHE=false`, `SANDBOX_MEMORY_LIMIT=4g`, `SANDBOX_FILES_DIR=/custom/files/dir` |
| **操作** | 重新加载 docker_utils 模块 |
| **预期输出** | `PIP_CACHE_PATH` = `/tmp/fake-cache`, `ENABLE_PIP_CACHE` = `False`, `SANDBOX_MEMORY_LIMIT` = `"4g"`, `SANDBOX_FILES_DIR` = `/custom/files/dir` |

#### `test_config_default_values`

| 项目 | 说明 |
|------|------|
| **目的** | 验证当没有环境变量时，程序使用正确的默认值 |
| **输入** | 清空所有环境变量 |
| **操作** | 重新加载 docker_utils 模块 |
| **预期输出** | `PIP_CACHE_PATH` = `None`, `ENABLE_PIP_CACHE` = `True` (默认开启), `SANDBOX_MEMORY_LIMIT` = `"2g"` (默认), `SANDBOX_FILES_DIR` = `None` (默认未设置) |

#### `test_sandbox_files_dir_empty_string_disables_persistence`

| 项目 | 说明 |
|------|------|
| **目的** | 验证设置 `SANDBOX_FILES_DIR=''` 会禁用文件持久化 |
| **输入** | 环境变量：`SANDBOX_FILES_DIR=""` (空字符串) |
| **操作** | 调用 `get_files_dir()` |
| **预期输出** | 返回 `None`，表示禁用持久化 |

#### `test_sandbox_files_dir_custom_path`

| 项目 | 说明 |
|------|------|
| **目的** | 验证用户自定义的文件保存路径会被使用 |
| **输入** | 环境变量：`SANDBOX_FILES_DIR=/my/custom/path` |
| **操作** | 调用 `get_files_dir()` |
| **预期输出** | 返回 `"/my/custom/path"` |

#### `test_sandbox_files_dir_auto_default`

| 项目 | 说明 |
|------|------|
| **目的** | 验证未设置 `SANDBOX_FILES_DIR` 时，自动使用系统临时目录 |
| **输入** | 不设置 `SANDBOX_FILES_DIR` 环境变量 |
| **操作** | 调用 `get_files_dir()` |
| **预期输出** | 返回系统临时目录下的路径，包含 `"python-sandbox-mcp"` 和 `"files"` |

---

### 2. test_docker_utils.py - Docker 工具函数测试

测试 Docker 操作、文件持久化核心逻辑和宿主机文件操作。

#### 基础功能测试

##### `test_is_docker_running_true`

| 项目 | 说明 |
|------|------|
| **目的** | 验证 Docker 运行状态检测（Docker 正常运行时） |
| **输入** | Mock Docker 客户端，返回正常响应 |
| **操作** | 调用 `is_docker_running()` |
| **预期输出** | 返回 `True` |

##### `test_is_docker_running_false`

| 项目 | 说明 |
|------|------|
| **目的** | 验证 Docker 运行状态检测（Docker 未运行时） |
| **输入** | Mock Docker 客户端，抛出异常 |
| **操作** | 调用 `is_docker_running()` |
| **预期输出** | 返回 `False` |

##### `test_exec_command_logic`

| 项目 | 说明 |
|------|------|
| **目的** | 验证在容器内执行命令的功能 |
| **输入** | Mock Docker 容器，`exec_run` 返回 `(exit_code=0, output=(b"hello", b""))` |
| **操作** | 调用 `exec_command("fake-id", "echo hello")` |
| **预期输出** | `exit_code=0`, `stdout="hello"`, `stderr=""` |

#### 文件持久化测试 (TestGetFilesDir 类)

##### `test_get_files_dir_returns_cached_value`

| 项目 | 说明 |
|------|------|
| **目的** | 验证 `get_files_dir()` 的缓存机制，避免重复计算 |
| **输入** | 清空环境变量，重置缓存状态 |
| **操作** | 连续两次调用 `get_files_dir()` |
| **预期输出** | 两次返回相同的路径值，且使用缓存 |

##### `test_get_files_dir_with_custom_path`

| 项目 | 说明 |
|------|------|
| **目的** | 验证使用自定义文件保存路径 |
| **输入** | 环境变量：`SANDBOX_FILES_DIR=/my/custom/path` |
| **操作** | 重置缓存后调用 `get_files_dir()` |
| **预期输出** | 返回 `"/my/custom/path"` |

##### `test_get_files_dir_disabled`

| 项目 | 说明 |
|------|------|
| **目的** | 验证禁用文件持久化功能 |
| **输入** | 环境变量：`SANDBOX_FILES_DIR=""` (空字符串) |
| **操作** | 重置缓存后调用 `get_files_dir()` |
| **预期输出** | 返回 `None`，表示禁用持久化 |

##### `test_get_files_dir_auto_default`

| 项目 | 说明 |
|------|------|
| **目的** | 验证智能默认模式，自动使用系统临时目录 |
| **输入** | 不设置 `SANDBOX_FILES_DIR` |
| **操作** | 重置缓存后调用 `get_files_dir()` |
| **预期输出** | 返回包含 `"python-sandbox-mcp"` 和 `"files"` 的系统临时目录路径 |

#### 宿主机文件读取测试 (TestReadFileFromHost 类)

##### `test_read_file_from_host_success`

| 项目 | 说明 |
|------|------|
| **目的** | 验证从宿主机持久化目录成功读取文件 |
| **输入** | 临时目录，包含 `test.txt` 文件，内容为 `"Hello from host!"` |
| **操作** | 设置 `SANDBOX_FILES_DIR` 为临时目录，调用 `read_file_from_host("test.txt")` |
| **预期输出** | 返回文件内容 `b"Hello from host!"` |

##### `test_read_file_from_host_not_found`

| 项目 | 说明 |
|------|------|
| **目的** | 验证当文件不存在时返回 None |
| **输入** | 临时目录（空），请求读取 `nonexistent.txt` |
| **操作** | 调用 `read_file_from_host("nonexistent.txt")` |
| **预期输出** | 返回 `None` |

##### `test_read_file_from_host_disabled`

| 项目 | 说明 |
|------|------|
| **目的** | 验证禁用持久化时，`read_file_from_host` 返回 None |
| **输入** | 环境变量：`SANDBOX_FILES_DIR=""` |
| **操作** | 调用 `read_file_from_host("test.txt")` |
| **预期输出** | 返回 `None` |

#### 宿主机文件列表测试 (TestListHostFiles 类)

##### `test_list_host_files_success`

| 项目 | 说明 |
|------|------|
| **目的** | 验证成功列出宿主机持久化目录中的所有文件 |
| **输入** | 临时目录，包含 `file1.txt`, `file2.txt` 和一个子目录 `subdir` |
| **操作** | 设置 `SANDBOX_FILES_DIR` 为临时目录，调用 `list_host_files()` |
| **预期输出** | 返回 `["file1.txt", "file2.txt"]` (只包含文件，不包含目录) |

##### `test_list_host_files_empty`

| 项目 | 说明 |
|------|------|
| **目的** | 验证空目录时返回空列表 |
| **输入** | 空的临时目录 |
| **操作** | 调用 `list_host_files()` |
| **预期输出** | 返回 `[]` |

##### `test_list_host_files_disabled`

| 项目 | 说明 |
|------|------|
| **目的** | 验证禁用持久化时，`list_host_files` 返回空列表 |
| **输入** | 环境变量：`SANDBOX_FILES_DIR=""` |
| **操作** | 调用 `list_host_files()` |
| **预期输出** | 返回 `[]` |

#### 状态管理测试 (TestResetFilesDir 类)

##### `test_reset_files_dir_clears_cache`

| 项目 | 说明 |
|------|------|
| **目的** | 验证 `reset_files_dir()` 能清除缓存，允许重新计算路径 |
| **输入** | 初始环境变量为空，然后修改为 `SANDBOX_FILES_DIR=/new/path` |
| **操作** | 1. 调用 `get_files_dir()` 获取初始路径<br>2. 修改环境变量<br>3. 调用 `reset_files_dir()`<br>4. 再次调用 `get_files_dir()` |
| **预期输出** | 第二次返回的路径与第一次不同，为 `/new/path` |

---

### 3. test_server.py - MCP Server 接口测试

测试 MCP Server 的工具接口和业务逻辑。

#### `test_search_pypi_packages_fallback`

| 项目 | 说明 |
|------|------|
| **目的** | 验证 PyPI 搜索的回退机制（当网页爬取失败时使用 JSON API） |
| **输入** | 搜索关键词 `"test-pkg"`<br>Mock 响应1：网页爬取返回空 HTML<br>Mock 响应2：JSON API 返回包信息 |
| **操作** | 调用 `search_pypi_packages("test-pkg")` |
| **预期输出** | 返回结果包含 `"test-pkg"` 和 `"Exact Match"` |

#### `test_run_python_ephemeral_error_no_docker`

| 项目 | 说明 |
|------|------|
| **目的** | 验证当 Docker 未运行时，`run_python_ephemeral` 返回正确的错误信息 |
| **输入** | Mock `is_docker_running()` 返回 `False`，代码 `print(1)` |
| **操作** | 调用 `run_python_ephemeral("print(1)")` |
| **预期输出** | 返回包含单个 `TextContent`，文本内容为 `"Docker is not running"` |

---

##  测试技术说明

### Mock 和补丁

测试大量使用 `unittest.mock` 的 `patch` 和 `MagicMock`:

```python
from unittest.mock import patch, MagicMock

# 模拟 Docker 客户端
with patch('docker.from_env') as mock_docker:
    mock_client = MagicMock()
    mock_docker.return_value = mock_client
    # 测试代码...
```

### 临时文件和目录

使用 `pytest` 的 `tmp_path` fixture 创建隔离的临时目录：

```python
def test_something(self, tmp_path):
    # tmp_path 是一个 Path 对象，指向临时目录
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    # 测试结束后自动清理
```

### 环境变量隔离

使用 `patch.dict` 确保测试之间不互相影响：

```python
with patch.dict(os.environ, {"SANDBOX_FILES_DIR": "/custom/path"}):
    # 在此块内，环境变量被修改
    result = get_files_dir()
# 退出块后，环境变量恢复
```

### 模块重新加载

测试配置时使用 `importlib.reload` 模拟模块首次加载：

```python
import importlib
import python_code_sandbox_mcp.docker_utils as docker_utils

with patch.dict(os.environ, {"NEW_VAR": "value"}):
    importlib.reload(docker_utils)
    # 模块现在使用新的环境变量
```

---

##  调试测试

### 打印详细信息

```bash
# 显示详细的测试输出
python -m pytest tests/ -v -s

# 在特定测试失败时停止
python -m pytest tests/ -x

# 运行上次失败的测试
python -m pytest tests/ --lf
```

### 使用 PDB

```python
def test_something():
    # 测试代码
    import pdb; pdb.set_trace()  # 在这里进入调试器
    # 更多代码
```

---

##  添加新测试

### 测试函数模板

```python
def test_new_feature():
    """
    测试新功能的描述
    
    目的: 验证 xxx 功能
    输入: xxx 条件
    操作: 执行 xxx
    预期: 返回 xxx
    """
    # 准备
    with patch('some.dependency') as mock:
        mock.return_value = expected_value
        
        # 执行
        result = function_under_test()
        
        # 验证
        assert result == expected_value
        mock.assert_called_once()
```

---

##  测试覆盖情况

| 模块 | 测试数 | 覆盖功能 |
|------|--------|----------|
| 配置模块 | 5 | 环境变量读取、默认值、三种持久化模式 |
| Docker 工具 | 14 | Docker 操作、文件持久化核心逻辑、宿主机文件操作 |
| Server 接口 | 2 | MCP 工具接口、错误处理 |
| **总计** | **21** | - |

---

##  相关文档

- [项目 README](../README.md)
- [使用指南](../docs/USAGE.md)
- [示例代码](../examples/README.md)

---

**最后更新**: 2026-01-29
