# 架构设计

## 概览

**Python Code Sandbox MCP** 采用了 **编排器模式 (Orchestrator Pattern)** 的设计。与传统的 Jupyter Kernel 网关不同，该服务器充当管理器的角色，按需供给和编排短暂的、隔离的执行环境。

## 核心组件

### 1. MCP 服务器 (`src/server.py`)
- 作为符合 Model Context Protocol (MCP) 的接口层。
- 向客户端（LLM, IDE）暴露工具。
- 管理请求的生命周期，但将实际执行委托给后端。
- 包含一个后台 **清理线程 (Scavenger Thread)**，用于监控并清理不活跃的容器，防止资源泄漏。

### 2. Docker 后端 (`src/docker_utils.py`)
- 使用 `docker` Python SDK 直接与本地 Docker 守护进程交互。
- 负责：
    - **容器生命周期**：`run` (运行), `stop` (停止), `remove` (删除)。
    - **代码注入**：与简单的 shell 执行不同，它使用 Base64 编码将 Python 代码安全地注入容器。
    - **依赖管理**：在运行中的容器内动态处理 `pip install` 操作。

## 数据流

1.  **请求**: 客户端发送 `run_python(code="print('hi')", container_id="...")`。
2.  **验证**: 服务器检查 `container_id` 是否存在于活跃注册表中。
3.  **执行**:
    - 代码被 Base64 编码。
    - 通过 `docker exec` 发送到容器。
    - 容器内的 Python 解释器解码并执行。
4.  **响应**: 捕获 `stdout` 和 `stderr` 并返回给客户端。

### 临时执行与文件检索 (`run_python_ephemeral`)

为了支持一次性任务和文件生成（如绘图），引入了临时执行流：
1.  **启动**: 启动一个新的容器。
2.  **执行**: 安装依赖并运行代码。
3.  **检索**: 扫描 `/workspace` 目录下的新文件。
4.  **读取**: 使用 `cat` 和 Base64 编码读取文件内容（区分文本和二进制/图像）。
5.  **销毁**: 无论成功与否，立即销毁容器。

## 状态管理

- **持久化**: `/workspace` 内的文件系统更改在容器的生命周期内持续存在。
- **会话范围**: `container_id` 定义了一个会话。一旦调用 `sandbox_stop` 或容器超时，所有状态将丢失。
- **并发**: 服务器使用线程安全的字典 (`active_sandboxes`) 来跟踪多个并发会话，允许不同用户或代理同时拥有自己隔离的环境。

