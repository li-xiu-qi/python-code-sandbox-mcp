#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 6: 

 SANDBOX_FILES_DIR 
"""

import asyncio
import tempfile
from pathlib import Path
from utils import (
    mcp_session, 
    get_server_params_with_custom_dir, 
    print_result,
    print_persistence_info
)


async def main():
    print("  6: ")
    print("=" * 60)
    
    # 
    custom_dir = Path(tempfile.gettempdir()) / "my_custom_sandbox_files"
    custom_dir.mkdir(exist_ok=True)
    
    print(f" : {custom_dir}")
    print("-" * 60)
    
    #  server 
    server_params = get_server_params_with_custom_dir(
        files_dir=str(custom_dir),
        memory_limit="512m"
    )
    
    code = '''
from datetime import datetime

# 
files = {
    'report.txt': f'Report generated at {datetime.now()}\\nStatus: OK',
    'data.csv': 'id,name,value\\n1,Alice,100\\n2,Bob,200',
    'notes.md': '# Session Notes\\n\\nThis file is saved to a custom directory.',
}

for filename, content in files.items():
    with open(filename, 'w') as f:
        f.write(content)
    print(f"Created: {filename}")

print("\\n All files created successfully!")
'''
    
    print("\n ...")
    
    async with mcp_session(server_params) as session:
        result = await session.call_tool("run_python_ephemeral", {
            "code": code,
            "dependencies": [],
            "image": "python:3.11-slim"
        })
        
        print_result(result, save_files=False)  # 
        
        print("\n :")
        for file_path in custom_dir.iterdir():
            if file_path.is_file():
                size = file_path.stat().st_size
                print(f"    {file_path.name} ({size} bytes)")
        
        print(f"\n : {custom_dir}")
        print("\n : ")


if __name__ == "__main__":
    asyncio.run(main())
