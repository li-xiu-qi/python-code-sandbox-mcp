# 故障排除与开发备忘 (Troubleshooting)

记录在项目开发和 CI/CD 过程中遇到的典型问题及其解决方案。

## 1. 代码规范 (Lint & Format)

### 问题：Ruff 检查失败
**现象**：CI 中的 `Lint and Format` 步骤报错，提示 `exit code 1`。
**原因**：
- 存在未使用的导入 (F401) 或变量 (F841)。
- 使用了裸 `except:` 块 (E722)，未指定具体异常。
- 代码格式不符合 PEP 8 规范（缩进、空格等）。

**解决**：
- 运行 `uv run ruff check . --fix` 自动修复逻辑问题。
- 运行 `uv run ruff format .` 强制格式化代码。

## 2. Docker 构建 (Docker Build)

### 问题：`uv sync` 参数错误
**现象**：报错 `unexpected argument '--system' found`。
**原因**：`uv sync` 命令不支持 `--system` 标志。
**解决**：在 Dockerfile 中设置环境变量 `ENV UV_SYSTEM_PYTHON=1` 替代该标志。

### 问题：找不到 README.md
**现象**：构建后端 `hatchling` 报错 `OSError: Readme file does not exist`。
**原因**：`pyproject.toml` 定义了 `readme = "README.md"`，但在执行 `uv sync` 时该文件尚未复制到容器。
**解决**：在执行同步命令前，确保 `COPY README.md .`。

### 问题：无法识别源码路径 (src 布局)
**现象**：报错 `ValueError: Unable to determine which files to ship`。
**原因**：项目使用 `src/` 目录结构，构建工具不知道如何映射包名。
**解决**：在 `pyproject.toml` 中添加：
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/python_code_sandbox_mcp"]
```

## 3. CI/CD (GitHub Actions)

### 问题：`uv` 虚拟环境找不到
**现象**：报错 `No virtual environment found`。
**原因**：在 CI 环境下，直接运行 `uv pip install` 缺少上下文。
**解决**：推荐使用 `uv run <cmd>`，它会自动管理临时环境并确保依赖就位。

### 问题：GitHub Actions 语法错误 (Unrecognized named-value: 'id')
**现象**：报错 `Unrecognized named-value: 'id'`，位于 `publish.yml`。
**原因**：错误地使用了 `${{ id.step_id.outputs }}`。GitHub Actions 的上下文对象应为 `steps`。
**解决**：将表达式修正为 `${{ steps.step_id.outputs }}`。

### 问题：Docker 登录失败 (Username and password required)
**现象**：在 `publish.yml` 步骤中报错登录失败。
**原因**：未在仓库 Secrets 中配置 `DOCKER_USERNAME`。
**解决**：推荐迁移至 **GHCR** (GitHub Container Registry)。使用内置的 `${{ github.actor }}` 和 `${{ secrets.GITHUB_TOKEN }}` 即可自动登录，无需手动配置密钥。

### 问题：GitHub Packages 权限拒绝
**现象**：推送到 GHCR 时报错权限不足。
**原因**：默认的 `GITHUB_TOKEN` 只有读取权限。
**解决**：在工作流文件的 Job 级别显式添加：
```yaml
permissions:
  packages: write
```

### 问题：Metadata Action 标签解析错误 (Unknown tag type attribute: latest)
**现象**：报错 `Unknown tag type attribute: latest`。
**原因**：YAML 多行字符串解析歧义或 `type=latest` 的特定限制。
**解决**：改用更稳健的 `type=raw,value=latest` 定义方式。
