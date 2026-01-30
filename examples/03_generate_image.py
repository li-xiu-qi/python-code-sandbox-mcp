#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 3: 




: 
- matplotlib_plot.png
-  output/ 
- 
"""

import asyncio
from pathlib import Path
from utils import mcp_session, get_server_params, save_image, print_persistence_info


async def main():
    print("  3: ")
    print("=" * 60)
    
    # 
    print_persistence_info()
    print()
    
    server_params = get_server_params(memory_limit="1g")
    
    #  matplotlib 
    code = '''
import matplotlib
matplotlib.use('Agg')  # 
import matplotlib.pyplot as plt
import numpy as np

print(" ...")

# 
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# 
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, y1, label='sin(x)', linewidth=2)
ax.plot(x, y2, label='cos(x)', linewidth=2, linestyle='--')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('Trigonometric Functions')
ax.legend()
ax.grid(True, alpha=0.3)

# 
plt.savefig('matplotlib_plot.png', dpi=150, bbox_inches='tight')
plt.close()

print("  matplotlib_plot.png")
print(" ")
'''
    
    dependencies = ["matplotlib", "numpy"]
    
    print(f" : {dependencies}")
    print("  run_python_ephemeral...")
    
    async with mcp_session(server_params) as session:
        result = await session.call_tool("run_python_ephemeral", {
            "code": code,
            "dependencies": dependencies,
            "image": "python:3.11-slim"
        })
        
        print("\n ...")
        
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        image_saved = False
        for content in result.content:
            if content.type == "text":
                print(f"\n :\n{content.text}")
            
            elif content.type == "image":
                print(f"\n   (MIME: {content.mimeType})")
                output_path = output_dir / "matplotlib_plot.png"
                save_image(content.data, str(output_path))
                image_saved = True
        
        if not image_saved:
            print("\n  ")
        else:
            print(f"\n : {output_path}")
            print(f"\n ")
            print(f"   ")


if __name__ == "__main__":
    asyncio.run(main())
