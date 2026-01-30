#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 1: 

 run_python_ephemeral  Python 


:
- 
- Windows: %TEMP%/python-sandbox-mcp/files/
- macOS/Linux: /tmp/python-sandbox-mcp/files/
"""

import asyncio
from utils import mcp_session, get_server_params, print_result, print_persistence_info


async def main():
    print("  1: ")
    print("=" * 60)
    
    # 
    print_persistence_info()
    print()
    
    # 
    server_params = get_server_params(memory_limit="512m")
    
    # 
    code = '''
import sys
from datetime import datetime

print("=" * 50)
print("Hello from Python Code Sandbox MCP!")
print("=" * 50)

print(f"\\n Python : {sys.version}")
print(f" : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 
a, b = 10, 20
print(f"\\n : {a} + {b} = {a + b}")
print(f" : {a} * {b} = {a * b}")

# 
with open('test_output.txt', 'w') as f:
    f.write(f"Test file created at {datetime.now()}\\n")
    f.write(f"Calculation result: {a} + {b} = {a + b}\\n")

print("\\n !")
print("  test_output.txt ")
'''
    
    print("  run_python_ephemeral...")
    print(f": {len(code)} ")
    
    async with mcp_session(server_params) as session:
        #  run_python_ephemeral 
        result = await session.call_tool("run_python_ephemeral", {
            "code": code,
            "dependencies": [],
            "image": "python:3.11-slim"
        })
        
        #  output/ 
        print_result(result, save_files=True, output_dir="output")
        
        print("\n : :")
        print("   1.  output/  MCP ")
        print("   2. ")


if __name__ == "__main__":
    asyncio.run(main())
