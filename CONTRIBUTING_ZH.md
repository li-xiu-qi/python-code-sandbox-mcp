# 贡献指南

感谢你对 Python Code Sandbox MCP 的关注！本项目旨在为 MCP 客户端提供最佳的 Python 执行环境。

## 开发设置

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/li-xiu-qi/python-code-sandbox-mcp.git
    cd python-code-sandbox-mcp
    ```

2.  **安装依赖**:
    我们使用 `uv` 进行依赖管理。
    ```bash
    uv sync
    ```

3.  **安装 pre-commit 钩子**:
    ```bash
    uv run pre-commit install
    ```

4.  **运行测试**:
    ```bash
    uv run pytest tests/
    ```

## 代码风格

我们使用 `ruff` 进行代码检查和格式化。这通过 pre-commit 和 CI 强制执行。你可以手动运行：
```bash
uv run ruff check . --fix
uv run ruff format .
```

## 合并请求 (PR) 流程

1.  确保所有测试均已通过。
2.  如果添加了新功能，请更新相关文档。
3.  遵循 [MIT 开源协议](LICENSE)。
