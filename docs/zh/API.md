# API 参考文档

Python Code Sandbox MCP 服务器提供的所有工具的完整参考。

## 概述

服务器提供以下工具：

| 工具 | 模式 | 描述 |
|------|------|-------------|
| `run_python_ephemeral` | 临时模式 | 在全新容器中一次性执行（推荐） |
| `sandbox_initialize` | 会话模式 | 启动持久化沙箱会话 |
| `run_python` | 会话模式 | 在现有会话中执行代码 |
| `sandbox_exec` | 会话模式 | 在沙箱中执行 shell 命令 |
| `sandbox_stop` | 会话模式 | 终止并移除沙箱 |
| `search_pypi_packages` | 工具 | 在 PyPI 上搜索包 |

---

## 临时模式工具

### `run_python_ephemeral`

在全新的一次性容器中执行 Python 代码。这是大多数用例的**推荐**方式。

#### 参数

| 名称 | 类型 | 必需 | 默认值 | 描述 |
|------|------|----------|---------|-------------|
| `code` | `string` | 是 | - | 要执行的 Python 源代码 |
| `dependencies` | `string[]` | 否 | `[]` | 执行前要安装的 pip 包列表 |
| `image` | `string` | 否 | `python:3.11-slim` | 容器使用的 Docker 镜像 |

#### 返回值

内容对象数组：

```typescript
[
  { type: "text", text: "..." },           // 控制台输出（stdout/stderr）
  { type: "image", data: "...", mimeType: "image/png" },  // 生成的图片
  { type: "text", text: "..." }            // 其他文件（文本或二进制信息）
]
```

#### 示例

```json
{
  "code": "import matplotlib.pyplot as plt; plt.plot([1,2,3]); plt.savefig('./files/chart.png')",
  "dependencies": ["matplotlib"],
  "image": "python:3.11-slim"
}
```

#### 执行流程

1. 使用指定镜像创建新容器
2. 安装依赖（如果指定）
3. 执行 Python 代码
4. 扫描 `/workspace` 查找生成的文件
5. 返回控制台输出和文件（图片作为 `image` 类型返回）
6. **自动销毁**容器

#### 错误处理

| 错误 | 描述 |
|-------|-------------|
| `Docker is not running` | Docker 守护进程未启动 |
| `Failed to install dependencies` | Pip 安装失败（无效的包名、网络问题） |
| `Execution failed` | Python 代码引发异常 |

#### 返回内容格式详解

`run_python_ephemeral` 返回 `List[Content]`，每个元素代表一种类型的内容：

**1. 控制台输出（TextContent）**

代码执行的标准输出（stdout）和标准错误（stderr）：

```json
{
  "type": "text",
  "text": "--- STDOUT ---\nHello World\n--- STDERR ---\nWarning message\n"
}
```

**格式说明**：
- 使用 `print()` 的内容会出现在 `--- STDOUT ---` 部分
- 使用 `print(..., file=sys.stderr)` 或异常信息会出现在 `--- STDERR ---` 部分
- 如果某部分没有输出，则不会显示该标记
- 中文内容支持良好，无需额外编码

**2. 图片文件（ImageContent）**

自动生成图表时返回，支持 `.png`、`.jpg`、`.jpeg`、`.gif`、`.webp`：

```json
{
  "type": "image",
  "data": "iVBORw0KGgoAAAANSUhEUgAAA...",
  "mimeType": "image/png"
}
```

**3. 文本文件（TextContent）**

代码创建的文本文件（.txt、.csv、.json 等）：

```json
{
  "type": "text",
  "text": "--- File: data.csv ---\nid,name,value\n1,Alice,100\n2,Bob,200\n"
}
```

**4. 二进制文件（TextContent）**

PDF、Word、Excel 等二进制文件（内容无法直接嵌入）：

```json
{
  "type": "text",
  "text": "--- File: report.pdf (Binary content, 45678 bytes) ---\n"
}
```

**注意**：二进制文件（如 PDF）不会返回实际内容，只会返回文件大小信息。如需获取 PDF 内容，有以下两种方式：

**方式一：启用文件持久化**（推荐）
设置 `SANDBOX_FILES_DIR` 环境变量，PDF 将保存到宿主机目录：
```bash
export SANDBOX_FILES_DIR="/path/to/save/files"
```

**方式二：在代码中转 base64**
在代码中将 PDF 转为 base64 并输出到 stdout：
```python
import base64
with open('report.pdf', 'rb') as f:
    print(base64.b64encode(f.read()).decode())
```

**完整响应示例**：

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

## 会话模式工具

会话模式允许你在多次执行之间保持状态。

### `sandbox_initialize`

启动新的持久化沙箱容器。

#### 参数

| 名称 | 类型 | 必需 | 默认值 | 描述 |
|------|------|----------|---------|-------------|
| `image` | `string` | 否 | `python:3.11-slim` | 容器使用的 Docker 镜像 |

#### 返回值

`string`：成功消息，包含容器 ID（例如：`Sandbox initialized. Container ID: abc123def456`）

#### 示例

```json
{
  "image": "python:3.11-slim"
}
```

#### 注意

- 容器保持运行直到调用 `sandbox_stop` 或超时（默认：1小时）
- 必须保存容器 ID 用于后续调用

---

### `run_python`

在现有沙箱会话中执行 Python 代码。

#### 参数

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `container_id` | `string` | 是 | `sandbox_initialize` 返回的容器 ID |
| `code` | `string` | 是 | 要执行的 Python 源代码 |
| `dependencies` | `string[]` | 否 | 要安装的 pip 包 |

#### 返回值

`string`：执行结果，包含以下部分（按顺序）：

1. **依赖安装信息**（如果有依赖）：`Installing dependencies: [...]`
2. **执行标记**：`Executing Python code...`
3. **执行结果**：包含 `--- Execution Result ---`、stdout 和 stderr

**返回格式示例**：

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

#### 示例

```json
{
  "container_id": "abc123def456",
  "code": "x = 42; print(x * 2)",
  "dependencies": ["numpy"]
}
```

#### 会话持久化

**重要澄清**: 会话模式保持的是**容器环境**和**文件系统状态**，而不是 Python 变量内存状态。

| 保持的内容 | 不保持的内容 |
|-----------|------------|
| [x] 已安装的包 | [ ] Python 变量（每次新进程） |
| [x] 创建的文件 | [ ] 内存状态 |
| [x] 工作目录中的文件 | [ ] 未保存的临时数据 |

**正确的状态共享方式**（通过文件）：

```python
# 调用 1: 创建数据并保存到文件
{"container_id": "abc123", "code": "import pandas as pd; df = pd.DataFrame({'a': [1,2,3]}); df.to_csv('data.csv')"}

# 调用 2: 从文件读取数据
{"container_id": "abc123", "code": "import pandas as pd; df = pd.read_csv('data.csv'); print(df.shape)"}  // 输出: (3, 1)
```

详见 [EXECUTION_MODES.md](./EXECUTION_MODES.md) 了解两种模式的详细区别。

---

### `sandbox_exec`

在沙箱中执行任意 shell 命令。

#### 参数

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `container_id` | `string` | 是 | 容器 ID |
| `command` | `string` | 是 | 要执行的 shell 命令 |

#### 返回值

`string`：包含以下部分：

```
Exit Code: 0
STDOUT:
<标准输出内容>

STDERR:
<标准错误内容>
```

**说明**：
- `Exit Code: 0` 表示命令成功执行，非零表示失败
- `STDOUT` 部分包含命令的标准输出
- `STDERR` 部分包含命令的错误输出（如果没有则为空）

#### 示例

```json
{
  "container_id": "abc123def456",
  "command": "pip list"
}
```

#### 常见用例

- 检查已安装的包：`pip list`
- 列出文件：`ls -la`
- 手动安装包：`pip install <package>`
- 检查 Python 版本：`python --version`

---

### `sandbox_stop`

终止并移除沙箱容器。

#### 参数

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `container_id` | `string` | 是 | 要停止的容器 ID |

#### 返回值

`string`：成功或错误消息

#### 示例

```json
{
  "container_id": "abc123def456"
}
```

#### 重要

- 容器中的所有数据将**永久删除**
- 使用完会话后始终调用此功能以释放资源

---

## 工具类

### `search_pypi_packages`

在 PyPI 上搜索 Python 包。

#### 参数

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `query` | `string` | 是 | 搜索词（例如 "pandas"、"machine learning"） |

#### 返回值

`string`：匹配的包列表，包含版本和描述（前 5 个结果）

#### 示例

```json
{
  "query": "data visualization"
}
```

#### 响应格式

```
- **matplotlib** (3.8.0): Comprehensive library for creating static, animated, and interactive visualizations
- **seaborn** (0.13.0): Statistical data visualization using matplotlib
- **plotly** (5.18.0): Interactive graphing library for Python
```

---

## 错误码和故障排除

### 常见错误

| 错误消息 | 原因 | 解决方案 |
|--------------|-------|----------|
| `Error: Docker is not running` | Docker 守护进程未启动 | 启动 Docker Desktop 或 Docker 服务 |
| `Container not found` | 无效的容器 ID 或容器已被清理 | 检查容器 ID，创建新会话 |
| `Failed to install dependencies` | 无效的包名、网络问题或依赖冲突 | 使用 `search_pypi_packages` 验证包名 |
| `Execution failed` | Python 代码引发异常 | 检查 stderr 中的错误跟踪 |
| `No such file or directory` | 尝试访问不存在的路径 | 验证代码中的文件路径 |

### 资源限制

所有容器的默认限制：

| 资源 | 默认值 | 可配置 |
|----------|---------|--------------|
| 内存 | 2GB | `SANDBOX_MEMORY_LIMIT` 环境变量 |
| CPU | 0.5 核 | `SANDBOX_CPU_QUOTA` 环境变量 |
| 最大生命周期 | 1 小时 | 不可配置（清理线程） |

---

## 最佳实践

### 何时使用临时模式与会话模式

**使用 `run_python_ephemeral` 的情况：**
- 运行一次性脚本
- 生成图表或文件
- 调用之间不需要保持状态
- 希望自动清理

**使用会话模式的情况：**
- 在多个步骤之间构建状态
- 安装许多依赖（避免重复安装）
- 交互式开发/调试
- 超过单次执行的长时任务

### 文件操作

**临时模式：**
```python
# 保存到 ./files/ 以确保被捕获
import matplotlib.pyplot as plt
plt.plot([1, 2, 3])
plt.savefig('./files/chart.png')  // 会被返回
plt.savefig('chart.png')          // 可能不会被捕获
```

**会话模式：**
```python
# 文件在会话期间持久化
with open('./files/data.txt', 'w') as f:
    f.write('persistent data')  // 在后续调用中可用
```

### 依赖管理

1. **先搜索**：使用 `search_pypi_packages` 验证确切的包名
2. **指定版本**（可选）：`numpy==1.24.0`
3. **启用缓存**：设置 `PIP_CACHE_PATH` 以加快重复安装

---

## 类型定义

### 内容类型

```typescript
interface TextContent {
  type: "text";
  text: string;
}

interface ImageContent {
  type: "image";
  data: string;        // Base64 编码
  mimeType: string;    // 例如 "image/png", "image/jpeg"
}

interface EmbeddedResource {
  type: "resource";
  resource: {
    text: string;
    uri?: string;
  };
}
```

