# Python Code Sandbox MCP - AGENTS.md

## 项目概述

**Python Code Sandbox MCP** 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的服务端实现，用于在临时的 Docker 容器中安全地执行 Python 代码。该项目采用**编排器模式 (Orchestrator Pattern)**，作为管理器按需供给和编排隔离的执行环境。

### 核心功能

- **隔离执行**: 在 ephemeral Docker 容器中运行代码（默认使用 `python:3.11-slim`）
- **一键执行 (One-Shot)**: 在一次性容器中运行脚本并立即获取结果
- **会话模式**: 保持容器运行，适用于复杂的、多步骤的交互任务
- **自动依赖管理**: 根据需求自动从 PyPI 安装指定的 pip 包
- **安全第一**: 支持 CPU/内存资源限制，容器内非 root 用户运行
- **文件回传**: 自动捕获脚本生成的图片（如绘图）和文件

## 技术栈

| 类别 | 技术 |
|------|------|
| 编程语言 | Python 3.10+ |
| 包管理器 | [uv](https://docs.astral.sh/uv/) |
| MCP 框架 | [FastMCP](https://github.com/modelcontextprotocol/python-sdk) |
| 容器化 | Docker + `docker` Python SDK |
| 数据验证 | Pydantic v2 |
| 代码质量 | Ruff (linter + formatter) |
| 安全审计 | pip-audit |
| 测试框架 | pytest + pytest-asyncio |
| 预提交钩子 | pre-commit |

## 项目结构

```
.
├── src/python_code_sandbox_mcp/    # 主源码目录
│   ├── __init__.py                 # 包初始化（空文件）
│   ├── server.py                   # MCP 服务器实现，暴露工具接口
│   └── docker_utils.py             # Docker 容器生命周期管理
├── tests/                          # 测试目录
│   ├── test_server.py              # 服务器接口测试
│   ├── test_docker_utils.py        # Docker 工具测试
│   └── test_config.py              # 配置加载测试
├── docs/                           # 文档（中英文双语）
│   ├── en/                         # 英文文档
│   │   ├── README.md               # 文档索引
│   │   ├── ARCHITECTURE.md         # 架构设计说明
│   │   ├── USAGE.md                # 使用指南
│   │   ├── API.md                  # API 参考
│   │   ├── EXAMPLES.md             # 使用示例
│   │   ├── EXECUTION_MODES.md      # 执行模式详解
│   │   ├── PERSISTENCE.md          # 文件持久化
│   │   ├── SECURITY.md             # 安全准则
│   │   ├── TROUBLESHOOTING.md      # 故障排除
│   │   └── changelog/              # 版本更新日志
│   └── zh/                         # 中文文档
│       └── ...                     # 同上（中文版本）
├── examples/                       # 客户端示例代码
│   ├── 01_basic_print.py
│   ├── 02_with_dependencies.py
│   ├── ...
│   └── utils.py
├── pyproject.toml                  # Python 项目配置（uv 使用）
├── uv.lock                         # 锁定依赖版本
├── Dockerfile                      # 容器镜像构建
├── server.yaml                     # MCP 服务器配置清单
├── .pre-commit-config.yaml         # 预提交钩子配置
└── .github/workflows/              # CI/CD 工作流
    ├── ci.yml                      # 持续集成
    └── publish.yml                 # 镜像发布
```

## 架构设计

### 核心组件

1. **MCP 服务器 (`server.py`)**
   - 使用 FastMCP 框架实现 MCP 协议接口
   - 暴露以下工具：
     - `run_python_ephemeral`: 在临时容器中执行一次性脚本（推荐）
     - `sandbox_initialize`: 启动持久化沙箱会话
     - `run_python`: 在现有会话中执行代码
     - `sandbox_exec`: 在沙箱中执行 shell 命令
     - `sandbox_stop`: 停止并移除沙箱
     - `search_pypi_packages`: 搜索 PyPI 包
   - 包含后台**清理线程 (Scavenger Thread)**，定期清理超过 1 小时的容器

2. **Docker 后端 (`docker_utils.py`)**
   - 使用 `docker` Python SDK 与本地 Docker 守护进程交互
   - 负责容器生命周期管理、代码注入、依赖管理、文件 I/O
   - 使用 **Base64 编码注入**机制安全传输代码到容器，避免 shell 转义问题

### 执行模式详解

项目支持两种执行模式，详细说明见 [EXECUTION_MODES.md](docs/en/EXECUTION_MODES.md)：

**临时模式 (`run_python_ephemeral`)**：
1. 创建新容器
2. 安装依赖（如指定）
3. 执行 Python 代码
4. 扫描 `/workspace` 目录获取生成的文件
5. 返回控制台输出和文件（图片自动识别）
6. **自动销毁容器**（无论成功与否）

**会话模式** (`sandbox_initialize` -> `run_python` -> `sandbox_stop`)：
1. 启动容器并获取 container_id
2. 在相同环境中多次执行代码
3. 通过**文件**共享状态（变量不会在内存中保持）
4. 手动停止或等待超时清理

**重要澄清**：会话模式保持的是容器环境和文件系统，不是 Python 变量内存状态。每次 `run_python` 调用都是新的 Python 进程。

### 执行流程

**临时执行模式 (`run_python_ephemeral`)**：
1. 创建新容器
2. 安装依赖（如指定）
3. 执行 Python 代码
4. 扫描 `/workspace` 目录获取生成的文件
5. 返回控制台输出和文件（图片自动识别）
6. **自动销毁容器**（无论成功与否）

**会话模式** (`sandbox_initialize` -> `run_python` -> `sandbox_stop`)：
1. 启动容器并获取 container_id
2. 在相同环境中多次执行代码，状态保持
3. 手动停止或等待超时清理

## 环境配置

### 必需环境

- **Docker**: 必须安装并运行 Docker Desktop 或 Docker 服务
- **Python**: 3.10+
- **uv**: 现代 Python 包管理器

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PIP_CACHE_PATH` | (无) | 宿主机 pip 缓存路径（推荐设置） |
| `ENABLE_PIP_CACHE` | `true` | 是否启用 pip 缓存 |
| `SANDBOX_MEMORY_LIMIT` | `2g` | 每个沙箱容器的内存限制 |
| `SANDBOX_CPU_PERIOD` | `100000` | CPU 周期（微秒） |
| `SANDBOX_CPU_QUOTA` | `50000` | CPU 配额（50000/100000 = 0.5 核） |
| `LOG_LEVEL` | `INFO` | 日志级别 |

配置可通过 `.env` 文件或环境变量传入。复制 `.env.sample` 到 `.env` 进行本地配置。

## 常用命令

### 开发命令

```bash
# 安装依赖（包含开发依赖）
uv sync --extra dev

# 运行测试
uv run pytest tests/

# 代码检查
uv run ruff check src/
uv run ruff format --check src/

# 自动修复格式问题
uv run ruff check src/ --fix
uv run ruff format src/

# 安全审计
uv run pip-audit

# 运行服务器（本地开发）
uv run python -m python_code_sandbox_mcp.server
```

### Docker 命令

```bash
# 构建镜像
docker build -t python-code-sandbox-mcp .

# 运行容器（需要挂载 Docker socket）
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e SANDBOX_MEMORY_LIMIT=1g \
  ghcr.io/li-xiu-qi/python-code-sandbox-mcp

# 预拉取基础镜像（加速首次执行）
docker pull python:3.11-slim
```

## 代码风格指南

### Python 代码规范

- 使用 **Ruff** 进行代码格式化和检查
- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 风格
- 最大行长度：默认（88 字符）
- 使用类型注解（Type Hints）
- 文档字符串使用中文（与现有代码保持一致）

### 重要约定

1. **代码注入安全**: 所有传入容器的代码必须通过 Base64 编码，避免 shell 注入
   ```python
   b64_code = base64.b64encode(code.encode("utf-8")).decode("utf-8")
   cmd = f"python -c \"import base64; exec(base64.b64decode('{b64_code}').decode('utf-8'))\""
   ```

2. **文件路径处理**: 容器内工作目录为 `/workspace`，持久化文件应写入 `./files/`

3. **错误处理**: 使用 try-except 捕获 Docker API 错误，转换为友好的错误消息

4. **日志记录**: 使用 `logging` 模块，logger 名称为 `__name__`

## 测试策略

### 测试结构

- **单元测试**: 使用 `unittest.mock` 模拟 Docker 客户端
- **异步测试**: 使用 `pytest-asyncio` 测试异步工具函数
- **配置测试**: 验证环境变量加载和默认值

### 运行测试

```bash
# 运行所有测试
uv run pytest tests/

# 带覆盖率报告
uv run pytest tests/ --cov=src/python_code_sandbox_mcp
```

### CI/CD 流程

GitHub Actions 工作流包括：
1. **Lint 任务**: Ruff 检查 + pip-audit 安全审计 + 单元测试
2. **Docker 测试**: 多架构（linux/amd64, linux/arm64）镜像构建测试

## 安全考虑

### 隔离模型

- 使用标准 Docker 容器进行隔离（非 VM 级虚拟化）
- 默认不挂载宿主机目录
- 容器具有互联网访问权限（用于 pip install）

### 资源限制

- **内存**: 默认 2GB
- **CPU**: 默认 0.5 核
- **磁盘**: 继承 Docker 默认存储限制（约 20GB）

### 代码安全

- 使用 Base64 编码传输代码，防止基本的 shell 注入攻击
- 容器内以非 root 用户运行（取决于基础镜像配置）
- **注意**: 恶意 Python 代码仍可能尝试利用内核漏洞（在最新 Docker 版本中可能性较低）

## 部署说明

### Docker 部署

镜像发布到 GitHub Container Registry (GHCR)：
```
ghcr.io/li-xiu-qi/python-code-sandbox-mcp:latest
```

### Claude Desktop 配置

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
        "ghcr.io/li-xiu-qi/python-code-sandbox-mcp"
      ]
    }
  }
}
```

## 开发注意事项

1. **Docker-in-Docker**: 服务器本身运行在容器中，但需要访问宿主机的 Docker socket 来启动兄弟容器

2. **缓存优化**: 建议设置 `PIP_CACHE_PATH` 指向宿主机目录，可大幅加速重复依赖安装

3. **容器清理**: 后台线程每 10 分钟检查一次，自动清理运行超过 1 小时的容器

4. **中文优先**: 项目文档和代码注释主要使用中文，新增代码应保持这一约定

5. **文档一致性**: 
   - 修改文档时同步更新中英文版本
   - 示例代码变更需更新 `examples/` 和 `docs/*/EXAMPLES.md`
   - 使用 `git status` 确认所有相关文件已纳入提交

6. **版本管理**:
   - 重大功能变更更新 `docs/*/changelog/vX.Y.Z.md`
   - 遵循语义化版本规范 (SemVer)
   - 发布时打 tag 触发 Docker 镜像构建

## 协作规则与偏好

### 文档维护规则

1. **双语同步**
   - 所有文档必须同时维护中英文版本
   - 修改英文文档后，必须同步更新对应的中文文档
   - 新功能文档先完成英文版，再翻译中文版

2. **文档变更追踪**
   - 文档修改需要在 `docs/zh/changelog/` 和 `docs/en/changelog/` 中记录
   - 重大文档结构调整需要单独提交，便于 review
   - 示例代码变更需要同步更新 `examples/` 目录和 `docs/*/EXAMPLES.md`

3. **链接有效性**
   - 文档内部链接使用相对路径
   - 跨文档引用需确保中英文版本链接正确
   - README 中的文档索引需要及时更新

### 代码提交规范

1. **提交信息格式**
   ```
   <type>: <subject>
   
   [optional body]
   ```
   
   常用 type：
   - `feat`: 新功能
   - `fix`: 修复
   - `docs`: 文档
   - `chore`: 构建/工具
   - `test`: 测试

2. **分批次提交原则**
   - 逻辑相关的变更作为一个批次
   - 文档更新与代码变更分开提交
   - 大文档重构拆分为多个小提交（便于 review 和回滚）

### 用户偏好设置

1. **代码风格**
   - 使用 Ruff 进行代码格式化（默认配置）
   - 中文文档为主，代码注释使用中文
   - 文档中避免使用 emoji，使用文字或 Markdown 标记（如 `[x]` `[ ]`）

2. **流程图规范**
   - 优先使用 Mermaid 语法绘制流程图
   - 复杂流程使用 subgraph 分组
   - 确保中英文文档中的流程图一致

3. **日志输出**
   - 使用 `logging` 模块而非 print
   - 日志级别：DEBUG 用于开发，INFO 用于生产
   - 错误信息使用中文（与项目风格一致）

### 审查清单

提交前检查：
- [ ] 代码通过 Ruff 检查
- [ ] 代码通过 Ruff 格式化（`ruff format src/`）
- [ ] 测试通过 `uv run pytest`
- [ ] 文档链接有效
- [ ] 中英文文档同步更新
- [ ] 变更记录在 changelog 中
- [ ] 无敏感信息泄露（如 token、密码）

### 代码格式化规范

**CI 要求**：所有代码必须通过 Ruff 检查和格式化才能合并。

#### Ruff 使用指南

**安装 Ruff**：
```bash
# 使用 pip
pip install ruff

# 或使用 uv（推荐）
uv add --dev ruff
```

**必备命令**（提交前必须执行）：
```bash
# 检查代码风格
ruff check src/

# 自动格式化代码（必须执行）
ruff format src/

# 或使用 uv
uv run ruff check src/
uv run ruff format src/
```

#### 格式规则说明

**1. 导入排序**（`I` 规则）
- 导入顺序：标准库 → 第三方库 → 本地模块
- 每组之间用空行分隔
- 每组内部按字母顺序排序

```python
# 标准库
import base64
import logging
from typing import List

# 第三方库
import httpx
from bs4 import BeautifulSoup

# 本地模块
from . import docker_utils
```

**2. 行长度限制**
- 最大行长度：88 字符
- 长字符串使用括号换行

```python
# 错误：超过 88 字符
mimeType=f"image/{lower_name.split('.')[-1] if lower_name.split('.')[-1] != 'jpg' else 'jpeg'}"

# 正确：拆分为多行
ext = lower_name.split('.')[-1]
mime_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"
```

**3. 其他格式要求**
- 行尾不能有空格或 Tab
- 文件必须以换行符（`\n`）结尾
- 使用 4 个空格缩进（不使用 Tab）
- 函数之间用两个空行分隔
- 类方法之间用一个空行分隔

#### 常见问题修复

**问题**：`Would reformat: src/xxx.py`
```bash
# 解决：直接运行格式化命令
ruff format src/
```

**问题**：导入排序错误
```bash
# 解决：使用 --fix 自动修复导入排序
ruff check src/ --fix
```

#### 手动修复（无 Ruff 环境）

如果暂时无法安装 Ruff，至少确保：
```python
def fix_basic_format(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除行尾空格
    lines = content.split('\n')
    fixed_lines = [line.rstrip() for line in lines]
    
    # 删除末尾多余空行，确保只有一个换行符结尾
    while fixed_lines and fixed_lines[-1] == '':
        fixed_lines.pop()
    
    fixed_content = '\n'.join(fixed_lines) + '\n'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
```

**注意**：手动修复只能解决最基本的格式问题，导入排序和长行拆分仍需 Ruff 处理。

#### 推荐：pre-commit 钩子

安装 pre-commit 实现自动格式化：
```bash
# 安装 pre-commit
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行检查（可选）
pre-commit run --all-files
```

配置 `.pre-commit-config.yaml`：
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## 参考链接

- [MCP 协议文档](https://modelcontextprotocol.io)
- [FastMCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [uv 文档](https://docs.astral.sh/uv/)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [项目 GitHub](https://github.com/li-xiu-qi/python-code-sandbox-mcp)
