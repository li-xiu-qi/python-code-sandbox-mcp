#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 4: 



:
- data.json
- report.txt
"""

import asyncio
from pathlib import Path
from utils import mcp_session, get_server_params, save_file


async def main():
    print("  4: ")
    print("=" * 60)
    
    server_params = get_server_params(memory_limit="512m")
    
    # 
    code = '''
import json
from datetime import datetime

print(" ...")

# 1.  JSON 
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

print(" : data.json")

# 2. 
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

print(" : report.txt")

# 3. 
print("\\n  data.json:")
with open('data.json', 'r', encoding='utf-8') as f:
    print(f.read())
'''
    
    print("\n  run_python_ephemeral...")
    
    async with mcp_session(server_params) as session:
        result = await session.call_tool("run_python_ephemeral", {
            "code": code,
            "dependencies": [],
            "image": "python:3.11-slim"
        })
        
        print("\n ...")
        
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        for content in result.content:
            if content.type == "text":
                text = content.text
                
                # 
                if text.startswith("--- File:"):
                    # 
                    filename = text.split("--- File:")[1].split("---")[0].strip()
                    file_content = text.split("---", 2)[2].strip()
                    
                    output_path = output_dir / filename
                    save_file(file_content, str(output_path))
                else:
                    print(f"\n :\n{text}")
        
        print(f"\n : {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
