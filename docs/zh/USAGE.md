# 使用指南

## 快速开始：使用 .env 文件 (推荐)

为了方便管理，你可以使用 `.env` 文件来配置服务器：
1. 在项目根目录将 `.env.sample` 复制并重命名为 `.env`。
2. 编辑 `.env` 文件，填入你的宿主机缓存路径。

### 完整环境变量参考

| 环境变量 | 必需 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `PIP_CACHE_PATH` | 推荐 | 无 | **宿主机**上的绝对路径，用于存储 pip 缓存。例如 `C:\Users\ke\.mcp-cache\pip` |
| `SANDBOX_FILES_DIR` | 可选 | 无 | **宿主机**上的绝对路径，用于持久化保存沙箱生成的文件。挂载至容器内 `./files/` |
| `ENABLE_PIP_CACHE` | 否 | `true` | 是否启用 pip 缓存。开启后，重复安装相同的库将极快 |
| `SANDBOX_MEMORY_LIMIT` | 否 | `2g` | 每个沙箱容器的最大内存限制（支持 `m`, `g` 单位） |
| `SANDBOX_CPU_PERIOD` | 否 | `100000` | CPU 周期，用于 CFS 调度器。与 `SANDBOX_CPU_QUOTA` 配合使用 |
| `SANDBOX_CPU_QUOTA` | 否 | `50000` | CPU 配额。`50000/100000` = 0.5 核。设为 `-1` 表示无限制 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别：`DEBUG`, `INFO`, `WARNING`, `ERROR` |

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

*注意：所有安装仅在当前容器生命周期内有效（除非使用了缓存目录）。*

## 数据持久化与生命周期

理解不同模式下的数据保存机制非常重要：

### 1. 临时模式 (`run_python_ephemeral`)
- **即用即销毁**: 每次调用都会创建一个**全新**的容器。
- **无状态**: 上一次调用中安装的库或定义的变量不会保留。
- **文件处理**: 执行结束后，服务器会扫描 `/workspace` 和 `./files/` 目录下的新文件并返回给客户端。

### 2. 会话模式 (`sandbox_initialize`)
- **会话内持久化**: 只要不调用 `sandbox_stop`，容器就会一直运行（直到超时）。
- **状态保留**: 你可以在第一步定义变量 `x=1`，在第二步打印 `print(x)`。

### 3. 宿主机持久化
通过设置 `SANDBOX_FILES_DIR` 环境变量，你可以实现跨容器的物理持久化：
- **挂载路径**: 宿主机目录会被映射到容器内的 `/workspace/files`。
- **使用方式**: 告诉模型将文件保存到 `./files/` 路径下。
- **效果**: 即使容器被销毁，保存在该目录下的文件也会留在宿主机硬盘上。

详细设计请参考 [PERSISTENCE.md](./PERSISTENCE.md)。

### 注意事项
如果不配置 `SANDBOX_FILES_DIR`，**没有任何**数据会持久化保存到宿主机的硬盘上。一旦容器被销毁，其中的数据将无法恢复。

## Docker 配置

服务器需要访问主机的 Docker 守护进程来生成兄弟容器。

- **挂载 Docker 套接字**: `-v /var/run/docker.sock:/var/run/docker.sock` 是必须的。
- **镜像**: 默认使用 `python:3.11-slim`。如果需要，你可以指定其他镜像，但请确保它们包含 `python` 和 `pip`。

## 高级配置

### 自定义 Docker 镜像

你可以通过传递 `image` 参数来使用自定义 Docker 镜像。对自定义镜像的要求：

1. **必须包含**: Python 和 pip 已安装并在 PATH 中可用
2. **工作目录**: 应设置为 `/workspace` 或类似路径
3. **可选**: 预装重量级依赖以加速执行

自定义镜像的 Dockerfile 示例：

```dockerfile
FROM python:3.11-slim

# 安装重量级依赖
RUN pip install torch torchvision transformers

# 设置工作目录
WORKDIR /workspace

# 可选：创建非 root 用户以提高安全性
RUN useradd -m -u 1000 sandbox
USER sandbox
```

构建并使用：
```bash
docker build -t my-custom-sandbox -f Dockerfile.custom .
```

然后在请求中使用：
```json
{
  "image": "my-custom-sandbox",
  "code": "import torch; print(torch.__version__)"
}
```

### 并发与多会话

服务器支持多个并发沙箱：

```python
# 会话 1: 数据处理
container_1 = sandbox_initialize()  # ID: abc123
run_python(container_1, code="import pandas; df1 = ...")

# 会话 2: 机器学习（同时进行）
container_2 = sandbox_initialize()  # ID: def456
run_python(container_2, code="import torch; model = ...")

# 每个会话完全隔离
```

**注意事项：**
- 每个容器消耗资源（内存、CPU）
- 总资源使用 = 所有活动容器的总和
- 后台清理独立运行在所有容器上

### 执行超时

**注意**: 目前没有针对单次代码执行的内置超时。容器有 1 小时的最大生命周期（自动清理），但单次代码执行可能无限期运行。

**解决方法：**

1. **在 Python 代码中添加超时：**
```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("执行超时")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 秒超时
try:
    # 你的代码
    pass
finally:
    signal.alarm(0)  # 取消超时
```

2. **手动清理**: 如果代码挂起，手动停止容器：
```bash
docker stop <container_id>
```

## 性能优化

### 首次执行慢？

首次运行可能较慢，原因包括：
1. Docker 镜像下载
2. 初始 pip 缓存填充
3. 容器启动开销

**优化技巧：**

1. **预拉取基础镜像：**
```bash
docker pull python:3.11-slim
```

2. **启用 pip 缓存：**
```bash
export PIP_CACHE_PATH="/home/user/.cache/pip"
```

3. **使用会话模式**进行多个相关任务，避免重复创建容器

4. **使用自定义镜像**预装重量级依赖（PyTorch、TensorFlow 等）

### 资源调优

内存密集型任务：
```bash
export SANDBOX_MEMORY_LIMIT=8g
export SANDBOX_CPU_QUOTA=200000  # 2 核
```

轻量级任务（节省资源）：
```bash
export SANDBOX_MEMORY_LIMIT=512m
export SANDBOX_CPU_QUOTA=25000   # 0.25 核
```

## 故障排除

- **"Docker is not running"**: 确保 Docker Desktop 已启动。
- **"Container not found"**: 容器可能已被后台清理程序（默认超时：1小时）清理或手动停止。
- **"No space left on device"**: 清理 Docker 卷和镜像：`docker system prune -a`
- **"Memory limit too low"**: 增加 `SANDBOX_MEMORY_LIMIT` 或优化代码以减少内存使用。
- **网络问题**: 确保容器可以访问互联网以安装 pip 包。

更多故障排除技巧，参见 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)。

## 延伸阅读

- [API 参考](./API.md) - 完整工具文档
- [示例](./EXAMPLES.md) - 实用代码示例
- [PERSISTENCE.md](./PERSISTENCE.md) - 文件持久化详情
- [SECURITY.md](./SECURITY.md) - 安全考虑

