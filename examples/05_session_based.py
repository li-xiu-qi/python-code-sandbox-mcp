#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 5: 

 sandbox_initialize 
 run_python 


1. sandbox_initialize - 
2. run_python - 
3. sandbox_exec -  shell 
"""

import asyncio
from utils import mcp_session, get_server_params


async def main():
    print("  5: ")
    print("=" * 60)
    
    server_params = get_server_params(memory_limit="1g")
    
    async with mcp_session(server_params) as session:
        #  1: 
        print("\n  1: ...")
        init_result = await session.call_tool("sandbox_initialize", {
            "image": "python:3.11-slim"
        })
        
        #  ID
        container_id = None
        for content in init_result.content:
            if content.type == "text":
                text = content.text
                print(f" : {text}")
                #  ID
                if "Container ID:" in text:
                    container_id = text.split("Container ID:")[1].strip()
        
        if not container_id:
            print("  ID")
            return
        
        print(f"  ID: {container_id[:12]}...")
        
        #  2: 
        print("\n  2:  pandas...")
        result2 = await session.call_tool("run_python", {
            "container_id": container_id,
            "code": "import pandas as pd; print(f'pandas {pd.__version__} installed')",
            "dependencies": ["pandas"]
        })
        
        for content in result2.content:
            if content.type == "text":
                print(content.text)
        
        #  3: 
        print("\n  3: ...")
        code3 = '''
import pandas as pd
import numpy as np

# 
data = {
    'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
    'age': [25, 30, 35, 28, 32],
    'salary': [50000, 60000, 75000, 55000, 70000],
    'department': ['IT', 'HR', 'IT', 'Sales', 'HR']
}

df = pd.DataFrame(data)
print(":")
print(df)

#  CSV
df.to_csv('employees.csv', index=False)
print("\\n  employees.csv")

# 
print("\\n:")
print(df.describe())
'''
        
        result3 = await session.call_tool("run_python", {
            "container_id": container_id,
            "code": code3,
            "dependencies": []  # 
        })
        
        for content in result3.content:
            if content.type == "text":
                print(content.text)
        
        #  4:  CSV 
        print("\n  4: ...")
        code4 = '''
import pandas as pd

# 
df = pd.read_csv('employees.csv')

print(":")
dept_stats = df.groupby('department').agg({
    'salary': ['mean', 'min', 'max', 'count']
}).round(2)
print(dept_stats)

print("\\n (>60000):")
high_earners = df[df['salary'] > 60000]
print(high_earners[['name', 'salary', 'department']])

# 
with open('analysis_report.txt', 'w') as f:
    f.write("EMPLOYEE ANALYSIS REPORT\\n")
    f.write("=" * 40 + "\\n\\n")
    f.write(f"Total Employees: {len(df)}\\n")
    f.write(f"Average Salary: ${df['salary'].mean():.2f}\\n")
    f.write(f"Age Range: {df['age'].min()} - {df['age'].max()}\\n")

print("\\n  analysis_report.txt")
'''
        
        result4 = await session.call_tool("run_python", {
            "container_id": container_id,
            "code": code4,
            "dependencies": []
        })
        
        for content in result4.content:
            if content.type == "text":
                print(content.text)
        
        #  5:  shell 
        print("\n  5: ...")
        result5 = await session.call_tool("sandbox_exec", {
            "container_id": container_id,
            "command": "ls -la"
        })
        
        for content in result5.content:
            if content.type == "text":
                print(content.text)
        
        #  6: 
        print("\n  6: ...")
        result6 = await session.call_tool("sandbox_exec", {
            "container_id": container_id,
            "command": "cat analysis_report.txt"
        })
        
        for content in result6.content:
            if content.type == "text":
                print(content.text)
        
        print("\n" + "=" * 60)
        print(" !")
        print("\n : ")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
