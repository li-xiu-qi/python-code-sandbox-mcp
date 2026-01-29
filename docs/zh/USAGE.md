# 使用指南

## 快速开始：使用 .env 文件 (推荐)

为了方便管理，你可以使用 `.env` 文件来配置服务器：
1. 在项目根目录将 `.env.sample` 复制并重命名为 `.env`。
2. 编辑 `.env` 文件，填入你的宿主机缓存路径。

### 核心配置项说明

| 环境变量 | 默认值 | 描述 |
| :--- | :--- | :--- |
| `PIP_CACHE_PATH` | (必填) | **宿主机**上的绝对路径，用于存储 pip 缓存。例如 `C:\Users\ke\.mcp-cache\pip`。 |
| `ENABLE_PIP_CACHE` | `true` | 是否启用 pip 缓存。开启后，重复安装相同的库将极快。 |
| `SANDBOX_MEMORY_LIMIT`| `2g` | 每个沙箱容器的最大内存限制（支持 `m`, `g` 单位）。 |
| `SANDBOX_CPU_QUOTA` | `50000` | CPU 配额。结合 `CPU_PERIOD`(100000) 使用，`50000` 代表限制为 0.5 核。 |
| `LOG_LEVEL` | `INFO` | 日志级别：`DEBUG`, `INFO`, `WARNING`, `ERROR`。 |

## 工具概览

### 1. `run_python_ephemeral` (推荐用于快速任务)
在全新的容器中执行脚本并立即获取结果。非常适合数据分析、绘图或快速计算。

**示例提示词:**
> "写一个 Python 脚本绘制正弦波并保存为 'sine.png'。"

**工作原理:**
1. 服务器启动一个临时容器。
2. 安装 `matplotlib` (如果需要)。
3. 运行代码。
4. 检测工作区中的 `sine.png`。
5. 返回图像数据和控制台输出。
6. 删除容器。

### 2. 会话模式 (`sandbox_initialize` -> `run_python` -> `sandbox_stop`)
当你需要跨多轮对话保持状态（变量、定义的函数）时使用此模式。

**工作流程:**
1. 调用 `sandbox_initialize()` -> 获取 `container_id`。
2. 调用 `run_python(container_id, code="x = 10")`。
3. 调用 `run_python(container_id, code="print(x + 5)")` -> 输出: `15`。
4. 完成后调用 `sandbox_stop(container_id)`。

### 3. `search_pypi_packages`
在安装之前查找包的确切名称。

**示例:**
> `search_pypi_packages(query="machine learning")`

## 执行机制与依赖管理

### 1. 代码是如何执行的？
为了确保代码能够安全且完整地传输到容器中，服务器采用了 **Base64 编码注入** 机制：
- 服务器将你的 Python 代码转换成 Base64 字符串。
- 通过 `docker exec` 发送一条类似 `python -c "import base64; exec(...)"` 的命令。
- 这样可以避免因代码中的特殊字符（引号、换行、转义符）导致 Shell 解析出错。

### 2. 依赖是如何安装的？
你有两种方式管理 Python 依赖：
- **自动安装（推荐）**: 在调用 `run_python` 或 `run_python_ephemeral` 时，在 `dependencies` 参数中传入包名列表。服务器会在运行代码前自动执行 `pip install`。
- **手动安装**: 使用 `sandbox_exec` 工具直接运行 `pip install <package_name>` 命令。

#### 性能优化：Pip 缓存
为了加快安装速度，你可以通过设置环境变量 `PIP_CACHE_PATH` 来开启持久化缓存：
- 将其设为宿主机上的一个绝对路径（例如：`/Users/yourname/.mcp/pip-cache`）。
- 开启后，重复安装相同的包将几乎瞬间完成。
- 你也可以通过设置 `ENABLE_PIP_CACHE=false` 来完全禁用缓存。

#### 资源限制
你可以通过以下环境变量调整沙箱的资源配额：
- `SANDBOX_MEMORY_LIMIT`: 内存限制（默认 `2g`）。
- `SANDBOX_CPU_PERIOD` 和 `SANDBOX_CPU_QUOTA`: CPU 配额控制。

*注意：所有安装仅在当前容器生命周期内有效（除非使用了缓存目录）。*

## 数据持久化与生命周期

理解不同模式下的数据保存机制非常重要：

### 1. 临时模式 (`run_python_ephemeral`)
- **即用即销毁**: 每次调用都会创建一个**全新**的容器。
- **无状态**: 上一次调用中安装的库或定义的变量不会保留。
- **文件处理**: 执行结束后，服务器会读取 `/workspace` 目录下的文件（如生成的图片）并返回给客户端，随后**立即销毁**容器和其中的所有数据。

### 2. 会话模式 (`sandbox_initialize`)
- **会话内持久化**: 只要不调用 `sandbox_stop`，容器就会一直运行（直到超时）。
- **状态保留**: 你可以在第一步定义变量 `x=1`，在第二步打印 `print(x)`。
- **文件暂存**: 你可以在容器内生成文件，并在后续步骤中读取或修改它们。
- **最终销毁**: 当你调用 `sandbox_stop` 或容器空闲超过 1 小时（被后台清理），容器及其数据将被**永久删除**。

### ⚠️ 注意事项
默认配置下，**没有**任何数据会持久化保存到宿主机的硬盘上。一旦容器被销毁，其中的数据将无法恢复。

## Docker 配置

服务器需要访问主机的 Docker 守护进程来生成兄弟容器。

- **挂载 Docker 套接字**: `-v /var/run/docker.sock:/var/run/docker.sock` 是必须的。
- **镜像**: 默认使用 `python:3.11-slim`。如果需要，你可以指定其他镜像，但请确保它们包含 `python` 和 `pip`。

## 故障排除

- **"Docker is not running"**: 确保 Docker Desktop 已启动。
- **"Container not found"**: 容器可能已被后台清理程序（默认超时：1小时）清理或手动停止。
- **网络问题**: 确保容器可以访问互联网以安装 pip 包。