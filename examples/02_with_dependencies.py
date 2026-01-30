#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 2: 

 pip 
"""

import asyncio
from utils import mcp_session, get_server_params, print_result


async def main():
    print("  2: ")
    print("=" * 60)
    
    server_params = get_server_params(memory_limit="1g")
    
    #  requests 
    code = '''
import requests
import json

print("=" * 60)
print(" HTTP ")
print("=" * 60)

print(f"\\n requests : {requests.__version__}")

#  API
url = "https://httpbin.org/get"
print(f"\\n  URL: {url}")

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    print(f" : {response.status_code}")
    print(f"\\n :")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\\n  (JSON):")
    print(json.dumps(data, indent=2))
    
except Exception as e:
    print(f" : {e}")

print("\\n !")
'''
    
    dependencies = ["requests"]
    
    print(f"\n : {dependencies}")
    print("  run_python_ephemeral...")
    
    async with mcp_session(server_params) as session:
        result = await session.call_tool("run_python_ephemeral", {
            "code": code,
            "dependencies": dependencies,
            "image": "python:3.11-slim"
        })
        
        print_result(result)


if __name__ == "__main__":
    asyncio.run(main())
