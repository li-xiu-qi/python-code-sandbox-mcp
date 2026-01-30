#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Client 

 MCP Server 
"""

import os
import base64
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def get_server_params(memory_limit: str = "1g", cpu_limit: str = "0.5") -> StdioServerParameters:
    """
     MCP Server 
    
    Args:
        memory_limit: 
        cpu_limit:  CPU 
    
    Returns:
        StdioServerParameters 
    """
    # 
    project_root = Path(__file__).parent.parent
    
    return StdioServerParameters(
        command="uv",
        args=["run", "--project", str(project_root), "python-code-sandbox", "stdio"],
        env={
            "SANDBOX_MEMORY_LIMIT": memory_limit,
            "SANDBOX_CPU_LIMIT": cpu_limit,
            # Windows Docker 
            "DOCKER_HOST": os.environ.get("DOCKER_HOST", ""),
            # 
            # "SANDBOX_FILES_DIR": "/path/to/your/files",
        }
    )


def get_server_params_with_custom_dir(files_dir: str, memory_limit: str = "1g", cpu_limit: str = "0.5") -> StdioServerParameters:
    """
     MCP Server 
    
    Args:
        files_dir: 
        memory_limit: 
        cpu_limit:  CPU 
    
    Returns:
        StdioServerParameters 
    """
    project_root = Path(__file__).parent.parent
    
    return StdioServerParameters(
        command="uv",
        args=["run", "--project", str(project_root), "python-code-sandbox", "stdio"],
        env={
            "SANDBOX_MEMORY_LIMIT": memory_limit,
            "SANDBOX_CPU_LIMIT": cpu_limit,
            "DOCKER_HOST": os.environ.get("DOCKER_HOST", ""),
            "SANDBOX_FILES_DIR": files_dir,  # 
        }
    )


def get_server_params_no_persistence(memory_limit: str = "1g", cpu_limit: str = "0.5") -> StdioServerParameters:
    """
     MCP Server 
    
    Args:
        memory_limit: 
        cpu_limit:  CPU 
    
    Returns:
        StdioServerParameters 
    """
    project_root = Path(__file__).parent.parent
    
    return StdioServerParameters(
        command="uv",
        args=["run", "--project", str(project_root), "python-code-sandbox", "stdio"],
        env={
            "SANDBOX_MEMORY_LIMIT": memory_limit,
            "SANDBOX_CPU_LIMIT": cpu_limit,
            "DOCKER_HOST": os.environ.get("DOCKER_HOST", ""),
            "SANDBOX_FILES_DIR": "",  # 
        }
    )


def get_docker_server_params(memory_limit: str = "1g", cpu_limit: str = "0.5") -> StdioServerParameters:
    """
     MCP Server Docker 
    
    Args:
        memory_limit: 
        cpu_limit:  CPU 
    
    Returns:
        StdioServerParameters 
    """
    return StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            "-e", f"SANDBOX_MEMORY_LIMIT={memory_limit}",
            "-e", f"SANDBOX_CPU_LIMIT={cpu_limit}",
            "ghcr.io/li-xiu-qi/python-code-sandbox-mcp"
        ],
        env={}
    )


@asynccontextmanager
async def mcp_session(server_params: StdioServerParameters):
    """
    MCP 
    
    Usage:
        async with mcp_session(server_params) as session:
            result = await session.call_tool(...)
    """
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def save_image(base64_data: str, filepath: str) -> None:
    """
     base64 
    
    Args:
        base64_data: base64 
        filepath: 
    """
    image_data = base64.b64decode(base64_data)
    Path(filepath).write_bytes(image_data)
    print(f" : {filepath}")


def save_file(content: str, filepath: str) -> None:
    """
    
    
    Args:
        content: 
        filepath: 
    """
    Path(filepath).write_text(content, encoding='utf-8')
    print(f" : {filepath}")


def print_result(result, save_files: bool = True, output_dir: str = "output") -> None:
    """
    
    
    Args:
        result: MCP CallToolResult 
        save_files: 
        output_dir: 
    """
    print("\n" + "=" * 60)
    print(" ")
    print("=" * 60)
    
    if result.isError:
        print(f" : {result.content}")
        return
    
    # 
    if save_files:
        Path(output_dir).mkdir(exist_ok=True)
    
    for i, content in enumerate(result.content, 1):
        print(f"\n  #{i} (: {content.type})")
        print("-" * 40)
        
        if content.type == "text":
            text = content.text
            print(text)
            
            # 
            if save_files and text.startswith("--- File:"):
                try:
                    filename = text.split("--- File:")[1].split("---")[0].strip()
                    file_content = text.split("---", 2)[2].strip() if "---" in text[10:] else text
                    filepath = Path(output_dir) / filename
                    save_file(file_content, str(filepath))
                except Exception as e:
                    print(f" : {e}")
        
        elif content.type == "image":
            print(f"[, MIME: {content.mimeType}]")
            print(f": {len(content.data)} bytes (base64)")
            
            if save_files:
                #  mimeType 
                ext = content.mimeType.split('/')[-1] if '/' in content.mimeType else 'png'
                if ext == 'jpeg':
                    ext = 'jpg'
                filepath = Path(output_dir) / f"image_{i}.{ext}"
                save_image(content.data, str(filepath))
        
        elif content.type == "resource":
            print(f"[: {content.resource.uri}]")
            if hasattr(content.resource, 'text'):
                print(f": {content.resource.text}")
        
        else:
            print(f"[: {content}]")
    
    print("\n" + "=" * 60)


def get_default_files_dir() -> str:
    """
    
    
    Returns:
        
    """
    import tempfile
    return str(Path(tempfile.gettempdir()) / "python-sandbox-mcp" / "files")


def print_persistence_info():
    """"""
    default_dir = get_default_files_dir()
    print(" :")
    print(f"   : {default_dir}")
    print("   :  SANDBOX_FILES_DIR ")
    print("   :  SANDBOX_FILES_DIR=''")
