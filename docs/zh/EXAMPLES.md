# 使用示例

本文档展示 Python Code Sandbox MCP 服务器的各种使用场景和代码示例。

> **提示**: 你也可以查看项目根目录的 `examples/` 文件夹，其中包含可运行的 Python 客户端示例代码。

## 目录

1. [基础示例](#基础示例)
2. [安装依赖](#安装依赖)
3. [生成图片](#生成图片)
4. [文件读写](#文件读写)
5. [会话模式](#会话模式)
6. [自定义文件目录](#自定义文件目录)
7. [无持久化模式](#无持久化模式)
8. [运行示例代码](#运行示例代码)

---

## 基础示例

### 示例 1: 基本打印输出

最简单的示例，展示如何在沙箱中执行 Python 代码并获取输出。

```python
import sys
from datetime import datetime

print("=" * 50)
print("Hello from Python Code Sandbox MCP!")
print("=" * 50)

print(f"\nPython 版本: {sys.version}")
print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 简单计算
a, b = 10, 20
print(f"\n计算: {a} + {b} = {a + b}")
print(f"计算: {a} * {b} = {a * b}")

# 创建文件（会被返回）
with open('test_output.txt', 'w') as f:
    f.write(f"Test file created at {datetime.now()}\n")
    f.write(f"Calculation result: {a} + {b} = {a + b}\n")

print("\n执行成功!")
print("文件已创建: test_output.txt")
```

**工具**: `run_python_ephemeral`  
**依赖**: 无  
**对应文件**: `examples/01_basic_print.py`

---

## 安装依赖

### 示例 2: 安装依赖并执行 HTTP 请求

展示如何在沙箱中安装 pip 依赖包，然后执行需要这些依赖的代码。

```python
import requests
import json

print("=" * 60)
print("HTTP 请求示例")
print("=" * 60)

print(f"\nrequests 版本: {requests.__version__}")

# 调用测试 API
url = "https://httpbin.org/get"
print(f"\n请求 URL: {url}")

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"\n响应头:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\n响应体 (JSON):")
    print(json.dumps(data, indent=2))
    
except Exception as e:
    print(f"错误: {e}")

print("\n请求完成!")
```

**工具**: `run_python_ephemeral`  
**依赖**: `["requests"]`  
**对应文件**: `examples/02_with_dependencies.py`

---

## 生成图片

### 示例 3: 生成 Matplotlib 图表

展示如何执行生成图片的代码，并从返回结果中获取图像数据。

```python
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import numpy as np

print("生成数据可视化图表...")

# 生成数据
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, y1, label='sin(x)', linewidth=2)
ax.plot(x, y2, label='cos(x)', linewidth=2, linestyle='--')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('Trigonometric Functions')
ax.legend()
ax.grid(True, alpha=0.3)

# 保存到文件（确保在 ephemeral 模式下被返回）
plt.savefig('matplotlib_plot.png', dpi=150, bbox_inches='tight')
plt.close()

print("图表已保存到 matplotlib_plot.png")
print("文件将被自动返回")
```

**工具**: `run_python_ephemeral`  
**依赖**: `["matplotlib", "numpy"]`  
**对应文件**: `examples/03_generate_image.py`  
**返回**: 控制台文本 + `ImageContent` 类型的图片数据

---

## 文件读写

### 示例 4: 创建和读取文件

展示如何在沙箱中创建多个文件，并从返回结果中读取文件内容。

```python
import json
from datetime import datetime

print("创建示例文件...")

# 1. 创建 JSON 文件
data = {
    "project": "Python Code Sandbox MCP",
    "version": "1.0.0",
    "created_at": datetime.now().isoformat(),
    "items": [
        {"id": 1, "name": "Item A", "value": 100},
        {"id": 2, "name": "Item B", "value": 200},
        {"id": 3, "name": "Item C", "value": 300}
    ],
    "metadata": {
        "author": "MCP User",
        "tags": ["demo", "json", "test"]
    }
}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("已创建: data.json")

# 2. 创建文本报告
report_content = f"""
========================================
        EXECUTION REPORT
========================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Environment: Python Code Sandbox MCP

SUMMARY:
--------
- Total Items: 3
- Total Value: 600
- Status: SUCCESS

DETAILS:
--------
All operations completed successfully.
Files created:
  1. data.json - Data file
  2. report.txt - This report

========================================
          END OF REPORT
========================================
"""

with open('report.txt', 'w', encoding='utf-8') as f:
    f.write(report_content)

print("已创建: report.txt")

# 3. 读取并显示文件内容
print("\n读取 data.json:")
with open('data.json', 'r', encoding='utf-8') as f:
    print(f.read())
```

**工具**: `run_python_ephemeral`  
**依赖**: 无  
**对应文件**: `examples/04_read_write_files.py`  
**返回**: 控制台文本 + 文件内容（以 `TextContent` 形式返回）

---

## 会话模式

### 示例 5: 持久化会话（多步骤执行）

展示如何使用 `sandbox_initialize` 创建持久化容器，然后多次执行代码，保持状态。

> **重要提示**: 会话模式保持的是**容器环境**和**文件系统**，而不是 Python 变量内存状态。每次 `run_python` 调用都是新的 Python 进程，变量不会自动保持。需要通过**文件**来共享状态。
>
> 详见 [EXECUTION_MODES.md](./EXECUTION_MODES.md) 了解详细区别。

#### 步骤 1: 初始化沙箱

```python
# 工具: sandbox_initialize
# 参数: {"image": "python:3.11-slim"}
# 返回: "Sandbox initialized. Container ID: abc123..."
```

**保存返回的 container_id，后续步骤使用。**

#### 步骤 2: 安装依赖（只执行一次）

```python
# container_id: "abc123..."
# dependencies: ["pandas"]

code = """
import pandas as pd
print(f'pandas {pd.__version__} 已安装')
"""
```

**工具**: `run_python`

#### 步骤 3: 创建数据

```python
# container_id: "abc123..."
# dependencies: [] (依赖已安装)

code = """
import pandas as pd
import numpy as np

# 创建示例数据
data = {
    'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
    'age': [25, 30, 35, 28, 32],
    'salary': [50000, 60000, 75000, 55000, 70000],
    'department': ['IT', 'HR', 'IT', 'Sales', 'HR']
}

df = pd.DataFrame(data)
print("数据创建完成:")
print(df)

# 保存到 CSV
df.to_csv('employees.csv', index=False)
print("\n已保存到 employees.csv")

# 数据统计
print("\n数据统计:")
print(df.describe())
"""
```

#### 步骤 4: 读取和分析数据

```python
# container_id: "abc123..."
# 注意: employees.csv 文件仍然存在！

code = """
import pandas as pd

# 读取之前创建的数据
df = pd.read_csv('employees.csv')

print("按部门统计:")
dept_stats = df.groupby('department').agg({
    'salary': ['mean', 'min', 'max', 'count']
}).round(2)
print(dept_stats)

print("\n高薪员工 (>60000):")
high_earners = df[df['salary'] > 60000]
print(high_earners[['name', 'salary', 'department']])

# 创建分析报告
with open('analysis_report.txt', 'w') as f:
    f.write("EMPLOYEE ANALYSIS REPORT\\n")
    f.write("=" * 40 + "\\n\\n")
    f.write(f"Total Employees: {len(df)}\\n")
    f.write(f"Average Salary: ${df['salary'].mean():.2f}\\n")
    f.write(f"Age Range: {df['age'].min()} - {df['age'].max()}\\n")

print("\n已创建: analysis_report.txt")
"""
```

#### 步骤 5: 执行 Shell 命令查看文件

```python
# 工具: sandbox_exec
# container_id: "abc123..."
# command: "ls -la"
```

返回:
```
Exit Code: 0
STDOUT:
total 24
drwxr-xr-x 1 root root 4096 Jan 29 10:00 .
drwxr-xr-x 1 root root 4096 Jan 29 09:00 ..
-rw-r--r-- 1 root root  120 Jan 29 10:00 employees.csv
-rw-r--r-- 1 root root  150 Jan 29 10:00 analysis_report.txt
```

#### 步骤 6: 停止沙箱

```python
# 工具: sandbox_stop
# container_id: "abc123..."
```

**对应文件**: `examples/05_session_based.py`

---

## 自定义文件目录

### 示例 6: 使用自定义文件保存目录

展示如何使用 `SANDBOX_FILES_DIR` 环境变量指定自定义的文件保存目录。

```python
from datetime import datetime

# 创建多个文件
files = {
    'report.txt': f'Report generated at {datetime.now()}\nStatus: OK',
    'data.csv': 'id,name,value\n1,Alice,100\n2,Bob,200',
    'notes.md': '# Session Notes\n\nThis file is saved to a custom directory.',
}

for filename, content in files.items():
    with open(filename, 'w') as f:
        f.write(content)
    print(f"Created: {filename}")

print("\nAll files created successfully!")
```

**工具**: `run_python_ephemeral`  
**依赖**: 无  
**对应文件**: `examples/06_custom_files_dir.py`  
**说明**: 设置 `SANDBOX_FILES_DIR=/your/custom/path` 指定自定义目录

---

## 无持久化模式

### 示例 7: 禁用文件持久化

展示如何设置 `SANDBOX_FILES_DIR=""` 来禁用文件持久化，文件仅存在于容器内。

```python
from datetime import datetime

# 创建临时文件
filename = 'temp_data.txt'
with open(filename, 'w') as f:
    f.write(f'Temporary data created at {datetime.now()}\n')
    f.write('This file will be lost when the container is destroyed.\n')

print(f"Created: {filename}")
print("注意: 此文件仅存在于容器内!")

# 读取文件内容
with open(filename, 'r') as f:
    print("\nFile content:")
    print(f.read())
```

**工具**: `run_python_ephemeral`  
**依赖**: 无  
**对应文件**: `examples/07_no_persistence.py`  
**说明**: 设置 `SANDBOX_FILES_DIR=""` 禁用持久化，文件不会保存到宿主机

---

## 更多示例

### 数据分析完整流程

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 生成销售数据
np.random.seed(42)
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
sales = np.random.randint(10000, 50000, 6)
profit = sales * np.random.uniform(0.2, 0.4, 6)

df = pd.DataFrame({
    'Month': months,
    'Sales': sales,
    'Profit': profit
})

# 计算利润率
df['Profit_Margin'] = (df['Profit'] / df['Sales'] * 100).round(2)

print("=== 销售数据 ===")
print(df)

print(f"\n总销售额: ${df['Sales'].sum():,}")
print(f"总利润: ${df['Profit'].sum():,.2f}")
print(f"平均利润率: {df['Profit_Margin'].mean():.2f}%")

# 可视化
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 销售额和利润对比
ax1.bar(df['Month'], df['Sales'], label='Sales', alpha=0.8)
ax1.bar(df['Month'], df['Profit'], label='Profit', alpha=0.8)
ax1.set_title('Sales vs Profit')
ax1.legend()

# 利润率趋势
ax2.plot(df['Month'], df['Profit_Margin'], marker='o', linewidth=2)
ax2.set_title('Profit Margin Trend (%)')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('./files/sales_report.png', dpi=150)
print("\n报告已保存到 ./files/sales_report.png")
```

**依赖**: `pandas`, `matplotlib`, `numpy`

---

### 图片处理

```python
from PIL import Image, ImageFilter
import numpy as np

# 创建渐变图像
width, height = 400, 300
gradient = np.zeros((height, width, 3), dtype=np.uint8)

for y in range(height):
    for x in range(width):
        gradient[y, x, 0] = int(255 * x / width)    # R
        gradient[y, x, 1] = int(255 * y / height)   # G
        gradient[y, x, 2] = 128                      # B

img = Image.fromarray(gradient)
img.save('./files/gradient.png')

# 应用滤镜
blurred = img.filter(ImageFilter.GaussianBlur(radius=5))
blurred.save('./files/blurred.png')

edges = img.filter(ImageFilter.FIND_EDGES)
edges.save('./files/edges.png')

print("生成了 3 张图片!")
```

**依赖**: `Pillow`, `numpy`

---

### 使用自定义 Docker 镜像

当你需要预装依赖时，可以构建自定义镜像：

```dockerfile
# Dockerfile.custom
FROM python:3.11-slim

# 预装重量级依赖
RUN pip install torch torchvision transformers

WORKDIR /workspace
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

---

## 运行示例代码

项目 `examples/` 目录包含完整的可运行 Python 客户端示例：

```bash
# 进入示例目录
cd examples

# 安装依赖
pip install mcp

# 运行示例
python 01_basic_print.py
python 02_with_dependencies.py
python 03_generate_image.py
python 04_read_write_files.py
python 05_session_based.py
python 06_custom_files_dir.py
python 07_no_persistence.py
```

详见 `examples/README.md` 了解更多信息。

---

## 最佳实践

### 1. 文件保存位置

在 ephemeral 模式下，始终将文件保存到当前目录或子目录：

```python
# 正确 - 会被扫描并返回
plt.savefig('chart.png')
plt.savefig('./files/report.png')

# 错误 - 可能不会返回（取决于扫描路径）
plt.savefig('/tmp/chart.png')
```

### 2. 依赖管理

- 使用 `search_pypi_packages` 验证包名
- 对于重量级依赖，考虑使用自定义镜像
- 在会话模式中，依赖只需安装一次

### 3. 错误处理

```python
import sys

try:
    # 你的代码
    result = risky_operation()
except Exception as e:
    print(f"错误: {e}", file=sys.stderr)
    sys.exit(1)
```

### 4. 调试技巧

```python
# 检查环境
import sys
print(f"Python: {sys.version}")
print(f"路径: {sys.path}")

# 列出已安装的包
import subprocess
subprocess.run([sys.executable, '-m', 'pip', 'list'])
```

