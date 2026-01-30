#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 7: 

 SANDBOX_FILES_DIR="" 


:
- 
- 
- 
"""

import asyncio
from pathlib import Path
from utils import (
    mcp_session, 
    get_server_params_no_persistence, 
    print_result,
    print_persistence_info
)


async def main():
    print("  7: ")
    print("=" * 60)
    
    print("  ")
    print("   ")
    print("-" * 60)
    
    #  server 
    server_params = get_server_params_no_persistence(memory_limit="512m")
    
    code = '''
from datetime import datetime

# 
filename = 'temp_data.txt'
with open(filename, 'w') as f:
    f.write(f'Temporary data created at {datetime.now()}\\n')
    f.write('This file will be lost when the container is destroyed.\\n')

print(f"Created: {filename}")
print("  This file exists only in the container!")

# 
with open(filename, 'r') as f:
    print("\\nFile content:")
    print(f.read())
'''
    
    print("\n ...")
    
    async with mcp_session(server_params) as session:
        result = await session.call_tool("run_python_ephemeral", {
            "code": code,
            "dependencies": [],
            "image": "python:3.11-slim"
        })
        
        print_result(result, save_files=True, output_dir="output")
        
        print("\n :")
        print("     MCP  output/ ")
        print("    ")
        print("    ")
        print("\n : ")


if __name__ == "__main__":
    asyncio.run(main())
