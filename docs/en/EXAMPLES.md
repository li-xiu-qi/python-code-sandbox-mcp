# Examples

Practical examples demonstrating various use cases of the Python Code Sandbox MCP server.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Data Analysis & Visualization](#data-analysis--visualization)
3. [Machine Learning](#machine-learning)
4. [Web Scraping](#web-scraping)
5. [File Processing](#file-processing)
6. [Multi-Step Workflows (Session Mode)](#multi-step-workflows-session-mode)
7. [Advanced Examples](#advanced-examples)

---

## Quick Start

### Hello World

```python
print("Hello from Python Sandbox!")
```

**Tool**: `run_python_ephemeral`

### Basic Math

```python
import math

# Calculate area of a circle
radius = 5
area = math.pi * radius ** 2
print(f"Area of circle with radius {radius}: {area:.2f}")
```

---

## Data Analysis & Visualization

### Example 1: Sine Wave Plot

Generate and save a sine wave chart.

```python
import numpy as np
import matplotlib.pyplot as plt

# Generate data
x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(x, y, 'b-', label='sin(x)')
plt.title('Sine Wave')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.grid(True)
plt.legend()

# Save to files directory (persistent)
plt.savefig('./files/sine_wave.png', dpi=150, bbox_inches='tight')
print("Chart saved to ./files/sine_wave.png")
```

**Dependencies**: `numpy`, `matplotlib`

---

### Example 2: Data Analysis with Pandas

```python
import pandas as pd
import matplotlib.pyplot as plt

# Create sample sales data
data = {
    'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    'Sales': [12000, 15000, 13000, 17000, 16000, 19000],
    'Expenses': [8000, 9000, 8500, 10000, 9500, 11000]
}
df = pd.DataFrame(data)

# Calculate profit
df['Profit'] = df['Sales'] - df['Expenses']

# Summary statistics
print("=== Sales Summary ===")
print(df.describe())

print("\n=== Monthly Profit ===")
print(df[['Month', 'Profit']])

# Create visualization
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Sales chart
axes[0].bar(df['Month'], df['Sales'], color='steelblue')
axes[0].set_title('Monthly Sales')
axes[0].set_ylabel('Amount ($)')

# Profit trend
axes[1].plot(df['Month'], df['Profit'], marker='o', color='green', linewidth=2)
axes[1].set_title('Profit Trend')
axes[1].set_ylabel('Profit ($)')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('./files/sales_analysis.png', dpi=150)
print("\nVisualization saved to ./files/sales_analysis.png")
```

**Dependencies**: `pandas`, `matplotlib`

---

### Example 3: Statistical Analysis

```python
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

# Generate sample data
np.random.seed(42)
group_a = np.random.normal(100, 15, 100)  # Mean=100, SD=15
group_b = np.random.normal(105, 20, 100)  # Mean=105, SD=20

# Descriptive statistics
print("=== Group A Statistics ===")
print(f"Mean: {np.mean(group_a):.2f}")
print(f"Median: {np.median(group_a):.2f}")
print(f"Std Dev: {np.std(group_a):.2f}")

print("\n=== Group B Statistics ===")
print(f"Mean: {np.mean(group_b):.2f}")
print(f"Median: {np.median(group_b):.2f}")
print(f"Std Dev: {np.std(group_b):.2f}")

# T-test
t_stat, p_value = stats.ttest_ind(group_a, group_b)
print(f"\n=== T-Test Results ===")
print(f"T-statistic: {t_stat:.4f}")
print(f"P-value: {p_value:.4f}")
print(f"Significant difference: {'Yes' if p_value < 0.05 else 'No'}")

# Visualization
plt.figure(figsize=(10, 6))
plt.hist(group_a, bins=20, alpha=0.6, label='Group A', color='blue')
plt.hist(group_b, bins=20, alpha=0.6, label='Group B', color='red')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title('Distribution Comparison')
plt.legend()
plt.savefig('./files/distribution_comparison.png', dpi=150)
```

**Dependencies**: `numpy`, `scipy`, `matplotlib`

---

## Machine Learning

### Example 4: Simple Linear Regression

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Generate sample data
np.random.seed(42)
X = np.random.rand(100, 1) * 10
y = 2 * X.squeeze() + 1 + np.random.randn(100) * 2  # y = 2x + 1 + noise

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Results
print("=== Model Results ===")
print(f"Coefficient: {model.coef_[0]:.4f}")
print(f"Intercept: {model.intercept_:.4f}")
print(f"MSE: {mean_squared_error(y_test, y_pred):.4f}")

# Visualization
plt.figure(figsize=(10, 6))
plt.scatter(X_test, y_test, color='blue', label='Actual', alpha=0.6)
plt.plot(X_test, y_pred, color='red', label='Predicted', linewidth=2)
plt.xlabel('X')
plt.ylabel('y')
plt.title('Linear Regression')
plt.legend()
plt.savefig('./files/linear_regression.png', dpi=150)
print("\nModel visualization saved to ./files/linear_regression.png")
```

**Dependencies**: `scikit-learn`, `numpy`, `matplotlib`

---

### Example 5: Classification with Iris Dataset

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
iris = load_iris()
X, y = iris.data, iris.target

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# Train classifier
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Predictions
y_pred = clf.predict(X_test)

# Results
print("=== Classification Report ===")
print(classification_report(y_test, y_pred, target_names=iris.target_names))

# Feature importance
print("\n=== Feature Importance ===")
for name, importance in zip(iris.feature_names, clf.feature_importances_):
    print(f"{name}: {importance:.4f}")

# Confusion matrix
plt.figure(figsize=(8, 6))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=iris.target_names,
            yticklabels=iris.target_names)
plt.title('Confusion Matrix')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.savefig('./files/confusion_matrix.png', dpi=150)
print("\nConfusion matrix saved to ./files/confusion_matrix.png")
```

**Dependencies**: `scikit-learn`, `matplotlib`, `seaborn`

---

## Web Scraping

### Example 6: Simple Web Scraping

```python
import requests
from bs4 import BeautifulSoup
import json

# Fetch a webpage
url = "https://quotes.toscrape.com/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract quotes
quotes = soup.find_all('div', class_='quote')

results = []
for quote in quotes[:5]:  # Get first 5 quotes
    text = quote.find('span', class_='text').get_text()
    author = quote.find('small', class_='author').get_text()
    tags = [tag.get_text() for tag in quote.find_all('a', class_='tag')]
    
    results.append({
        'quote': text,
        'author': author,
        'tags': tags
    })

# Save results
with open('./files/quotes.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Scraped {len(results)} quotes")
print("\nFirst quote:")
print(json.dumps(results[0], indent=2))
```

**Dependencies**: `requests`, `beautifulsoup4`

---

## File Processing

### Example 7: CSV Processing

```python
import pandas as pd

# Create sample CSV data
csv_data = """Name,Age,City,Salary
Alice,30,New York,70000
Bob,25,Los Angeles,50000
Charlie,35,Chicago,80000
Diana,28,Boston,65000
Eve,32,Seattle,75000"""

# Write to file
with open('./files/input.csv', 'w') as f:
    f.write(csv_data)

# Read and process
df = pd.read_csv('./files/input.csv')

print("=== Original Data ===")
print(df)

# Analysis
print("\n=== Salary Statistics ===")
print(df['Salary'].describe())

# Filter high earners
high_earners = df[df['Salary'] > 60000]
print("\n=== High Earners (> $60k) ===")
print(high_earners)

# Save filtered results
high_earners.to_csv('./files/high_earners.csv', index=False)
print("\nFiltered results saved to ./files/high_earners.csv")
```

**Dependencies**: `pandas`

---

### Example 8: Image Processing

```python
from PIL import Image, ImageFilter
import numpy as np

# Create a sample image (gradient)
width, height = 400, 300
gradient = np.zeros((height, width, 3), dtype=np.uint8)

# Create a colorful gradient
for y in range(height):
    for x in range(width):
        gradient[y, x, 0] = int(255 * x / width)    # Red
        gradient[y, x, 1] = int(255 * y / height)   # Green
        gradient[y, x, 2] = 128                      # Blue

img = Image.fromarray(gradient)
img.save('./files/original_gradient.png')

# Apply filters
blurred = img.filter(ImageFilter.GaussianBlur(radius=5))
blurred.save('./files/blurred_gradient.png')

edges = img.filter(ImageFilter.FIND_EDGES)
edges.save('./files/edges_gradient.png')

print("Created 3 images:")
print("- ./files/original_gradient.png")
print("- ./files/blurred_gradient.png")
print("- ./files/edges_gradient.png")
```

**Dependencies**: `Pillow`, `numpy`

---

## Multi-Step Workflows (Session Mode)

Session mode is ideal for complex workflows that require multiple steps with state preservation.

> **Important**: Session mode persists the **container environment** and **filesystem**, not Python variable memory state. Each `run_python` call starts a new Python process. Variables are not automatically preserved. Share state through **files**.
>
> See [EXECUTION_MODES.md](./EXECUTION_MODES.md) for detailed differences between modes.

### Example 9: Incremental Data Analysis

**Step 1**: Initialize sandbox and load data

```python
# Tool: sandbox_initialize
# Returns: container_id (save this!)
```

**Step 2**: Install dependencies and load data

```python
import pandas as pd
import numpy as np

# Load sample dataset
data = {
    'Product': ['A', 'B', 'C', 'D', 'E'] * 20,
    'Region': ['North', 'South', 'East', 'West'] * 25,
    'Sales': np.random.randint(1000, 10000, 100),
    'Quantity': np.random.randint(10, 100, 100)
}

df = pd.DataFrame(data)
df['Revenue'] = df['Sales'] * df['Quantity']

print(f"Loaded {len(df)} records")
print(df.head())
```

**Step 3**: Explore data

```python
print("=== Data Overview ===")
print(df.describe())

print("\n=== Sales by Region ===")
print(df.groupby('Region')['Revenue'].sum().sort_values(ascending=False))
```

**Step 4**: Create visualization

```python
import matplotlib.pyplot as plt

# Sales by product
product_sales = df.groupby('Product')['Revenue'].sum()

plt.figure(figsize=(10, 6))
product_sales.plot(kind='bar', color='steelblue')
plt.title('Revenue by Product')
plt.ylabel('Revenue ($)')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('./files/revenue_by_product.png')
print("Chart saved!")
```

**Step 5**: Clean up

```python
# Tool: sandbox_stop
# container_id: <your_container_id>
```

---

## Advanced Examples

### Example 10: Custom Docker Image

When you need pre-installed dependencies:

```dockerfile
# Dockerfile.custom
FROM python:3.11-slim

# Pre-install heavy dependencies
RUN pip install torch torchvision numpy pandas matplotlib

WORKDIR /workspace
```

Build and use:

```bash
docker build -f Dockerfile.custom -t my-custom-sandbox .
```

Then in your request:

```json
{
  "image": "my-custom-sandbox",
  "code": "import torch; print(torch.__version__)"
}
```

---

### Example 11: Generating Multiple Output Types

```python
import matplotlib.pyplot as plt
import json

# Generate data
x = range(10)
y = [i**2 for i in x]

# 1. Create plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, marker='o')
plt.title('Square Numbers')
plt.savefig('./files/square_numbers.png')

# 2. Save data as JSON
data = {'x': list(x), 'y': y}
with open('./files/data.json', 'w') as f:
    json.dump(data, f, indent=2)

# 3. Save as CSV
import csv
with open('./files/data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['x', 'y'])
    writer.writerows(zip(x, y))

print("Generated 3 files:")
print("- square_numbers.png (chart)")
print("- data.json (JSON data)")
print("- data.csv (CSV data)")
```

**Dependencies**: `matplotlib`

---

## Tips and Best Practices

### Performance Optimization

1. **Use pip cache**: Set `PIP_CACHE_PATH` environment variable
2. **Pre-built images**: For heavy dependencies (PyTorch, TensorFlow), use custom images
3. **Session mode**: Install dependencies once, run multiple times

### File Handling

1. Always use `./files/` prefix for files you want to keep
2. Check available disk space for large file operations
3. Clean up temporary files to avoid bloat

### Debugging

```python
# Check Python version
import sys
print(sys.version)

# List installed packages
import subprocess
subprocess.run(['pip', 'list'])

# Check available memory
import psutil
print(f"Available memory: {psutil.virtual_memory().available / 1e9:.2f} GB")
```

**Dependencies**: `psutil`

