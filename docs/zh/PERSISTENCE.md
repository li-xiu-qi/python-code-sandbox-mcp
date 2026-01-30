# 文件持久化设计

本文档说明了 Python Code Sandbox MCP 服务器中文件持久化的设计实现。

## 1. 核心目标
为了确保沙箱容器销毁后，生成的关键数据（如分析图表、生成的代码文件或处理后的数据集）仍能在宿主机上保留。

## 2. 实现方案
我们参考了 Node.js 版本的实现，采用了 **Docker 挂载卷 (Bind Mounts)** 技术。

### 目录映射关系
*   **宿主机路径**: 由环境变量 `SANDBOX_FILES_DIR` 指定。
*   **容器内路径**: 固定为 `/workspace/files`。

### 自动挂载逻辑
1.  启动沙箱时，系统检查 `SANDBOX_FILES_DIR` 是否已设置。
2.  若已设置，系统会自动在宿主机上创建该目录（如果不存在）。
3.  启动命令中加入卷挂载参数：`-v <宿主机路径>:/workspace/files:rw`。

## 3. 使用指南

### 开发者配置
在启动 MCP 服务器前，需设置环境变量：
```bash
# Windows (PowerShell)
$env:SANDBOX_FILES_DIR = "C:\Users\YourName\Desktop\sandbox-output"

# Linux / macOS
export SANDBOX_FILES_DIR="/home/user/sandbox-output"
```

### AI 模型使用
工具描述中已明确告知模型：**“如果你需要持久化保存文件，请将其写入 `./files/` 目录。”**

示例 Python 代码：
```python
import os

# 确保目录存在（容器内默认已挂载）
os.makedirs("files", exist_ok=True)

with open("files/report.txt", "w") as f:
    f.write("这是持久化保存的内容")
```

## 4. 文件回传机制
在 `run_python_ephemeral`（临时执行）模式下：
1.  脚本执行完成后，系统会递归扫描 `/workspace`（深度为 2）。
2.  位于 `files/` 目录下的新文件不仅会保存在宿主机，还会被读取并以 Base64 或文本形式回传给模型。
3.  系统会自动过滤 `.pycache` 和隐藏文件。

## 5. 使用场景对比

### 禁用持久化（默认不设置或设置为空字符串）

**适用于：打印即可获取信息的场景**

| 场景 | 示例 | 适用原因 |
|------|------|---------|
| 文本处理 | 数据分析、日志处理、文本生成 | 结果直接 `print()` 输出，或写入文本文件返回 |
| 简单图表 | matplotlib 折线图、柱状图 | 返回 `ImageContent`，LLM 可直接查看 |
| 计算验证 | 算法测试、数学计算 | 只需要 stdout 的结果 |
| API 调用 | 爬虫、HTTP 请求 | 返回 JSON/text 数据 |

**核心特点**：结果立即在响应中可见，无需在容器销毁后访问文件。

```python
# 示例：文本分析 - 适合禁用持久化
import pandas as pd
df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
print(df.describe())  # 直接打印，完事儿
```

**重要限制**：二进制文件（PDF、Word、Excel 等）在禁用持久化时无法获取内容。工具只返回文件大小信息，不返回内容：

```
--- File: report.pdf (Binary content, 45678 bytes) ---
```

如果需要在禁用持久化的情况下访问二进制文件内容，必须在代码中将其转为 base64 并输出到 stdout。

### 启用持久化（设置 SANDBOX_FILES_DIR）

**适用于：需要保留文件的场景**

| 场景 | 示例 | 适用原因 |
|------|------|---------|
| 二进制文档生成 | PDF 报告、Word 文档、Excel 表格 | 需要在容器销毁后访问文件 |
| 批量图片处理 | 生成多个图表、图片流水线 | 结果需要事后查看或处理 |
| 中间产物 | 模型检查点、临时数据集 | 文件用于后续处理步骤 |
| 长期存档 | 分析报告、生成的代码 | 结果需要保留供将来参考 |

```python
# 示例：二进制报告生成 - 需要持久化
import pandas as pd
df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
df.to_excel('report.xlsx')  # 二进制文件，需要持久化才能事后读取
print("Report generated")
```

### 一句话总结

- **禁用持久化** = "即算即走"模式，适合一次性任务，结果看一眼就完事儿。
- **启用持久化** = "工作台"模式，适合需要保留中间产物、事后反复查看的场景。

## 6. 注意事项

*   如果未配置 `SANDBOX_FILES_DIR`，`/workspace/files` 将仅作为容器内的普通目录存在，容器销毁后数据将丢失。
*   请确保宿主机路径具有读写权限。
*   二进制文件（PDF、Word、Excel 等）在禁用持久化时只能通过响应获取大小信息，无法获取内容。

