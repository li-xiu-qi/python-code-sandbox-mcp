# 🐍🚀 Python 代码沙箱 MCP 服务端

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)

基于模型上下文协议 (MCP) 的 Python 运行环境。支持在临时 Docker 容器中执行任意 Python 代码，并支持即时安装 pip 依赖。

## 核心特性

- **隔离执行**：在临时 Docker 容器中运行代码（默认使用 `python:3.11-slim`）。
- **一键执行 (One-Shot)**：在一次性容器中运行脚本并立即获取结果。
- **会话模式**：保持容器运行，适用于复杂的、多步骤的交互任务。
- **自动依赖管理**：根据需求自动从 PyPI 安装指定的 pip 包。
- **安全第一**：支持 CPU/内存资源限制，容器内非 root 用户运行。
- **文件回传**：自动捕获脚本生成的图片（如绘图）和文件。

## ⚠️ 前提条件

必须在本地安装并运行 Docker。

**提示**：建议预先拉取基础镜像以避免首次运行时的延迟：
```bash
docker pull python:3.11-slim
```

## 快速开始

### 在 Claude Desktop 中使用

将以下配置添加到你的 `claude_desktop_config.json` 文件中：

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
        "li-xiu-qi/python-code-sandbox-mcp"
      ]
    }
  }
}
```

### 手动运行 (Docker)

```bash
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e SANDBOX_MEMORY_LIMIT=1g \
  li-xiu-qi/python-code-sandbox-mcp
```

## 配置说明

服务端支持通过环境变量或 `.env` 文件进行配置。核心选项：

- `PIP_CACHE_PATH`：(推荐) 宿主机上的绝对路径，用于持久化 pip 缓存。
- `SANDBOX_MEMORY_LIMIT`：每个容器的最大内存限制（默认 `2g`）。
- `ENABLE_PIP_CACHE`：设为 `false` 可禁用缓存。

完整参数列表请参阅 [使用指南](docs/zh/USAGE.md)。

## 工具说明

### `run_python_ephemeral` (推荐)
在一个全新的、一次性的容器中运行单次 Python 脚本。

**输入参数：**
- `code` (string, 必填): 要执行的 Python 源码。
- `dependencies` (array of strings, 可选): 需要安装的 Pip 包名（例如：`["pandas", "matplotlib"]`）。

**执行逻辑：**
1. 创建全新的容器。
2. 安装指定的依赖包。
3. 执行脚本并捕获标准输出/错误。
4. 自动返回生成的文件（图片返回为 `image`，其他文件返回为 `resource`）。
5. 运行结束后自动销毁容器。

### `sandbox_initialize` / `run_python`
启动持久化沙箱，并在同一个环境中运行多个脚本。

## 测试提示词

连接成功后，可以尝试以下提示词进行验证：

1. **基础测试**：`编写并运行一个 Python 脚本，打印 "Hello MCP"`
2. **绘图测试**：`安装 matplotlib 并绘制一个正弦波图像，保存为 'sine.png'`

## 项目文档

- [详细使用指南](docs/zh/USAGE.md)
- [架构设计说明](docs/zh/ARCHITECTURE.md)
- [安全准则](docs/zh/SECURITY.md)
- [故障排除手册](docs/zh/TROUBLESHOOTING.md)

## 开源协议
MIT