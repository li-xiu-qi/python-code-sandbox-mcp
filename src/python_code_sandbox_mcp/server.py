import base64
import logging
import threading
import time
from typing import List, Union

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field

import mcp.types as types

from . import docker_utils

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("python-code-sandbox")

# Initialize FastMCP
mcp = FastMCP("python-code-sandbox")


@mcp.tool()
async def sandbox_initialize(image: str = "python:3.11-slim") -> str:
    """
    启动一个新的运行 Python 的隔离 Docker 容器。
    返回容器 ID，必须用于后续的执行请求。

    Args:
        image: 要使用的 Docker 镜像（默认：python:3.11-slim）
    """
    if not docker_utils.is_docker_running():
        return "Error: Docker is not running. Please start Docker Desktop."

    try:
        container_id = docker_utils.start_sandbox(image=image)
        return f"Sandbox initialized. Container ID: {container_id}"
    except Exception as e:
        return f"Failed to initialize sandbox: {str(e)}"


@mcp.tool()
async def sandbox_exec(container_id: str, command: str) -> str:
    """
    在运行的沙箱容器内执行原始 shell 命令。

    Args:
        container_id: 沙箱容器的 ID。
        command: 要执行的 shell 命令（例如 'ls -la', 'pip list'）。
    """
    try:
        exit_code, stdout, stderr = docker_utils.exec_command(container_id, command)
        output = f"Exit Code: {exit_code}\n"
        if stdout:
            output += f"STDOUT:\n{stdout}\n"
        if stderr:
            output += f"STDERR:\n{stderr}\n"
        return output
    except Exception as e:
        return f"Execution failed: {str(e)}"


@mcp.tool()
async def run_python(
    container_id: str, code: str, dependencies: List[str] = Field(default_factory=list)
) -> str:
    """
    在运行的沙箱容器内安装依赖项并执行 Python 代码。

    文件默认会持久化到宿主机的临时目录：
    - Windows: %TEMP%/python-sandbox-mcp/files/
    - macOS/Linux: /tmp/python-sandbox-mcp/files/

    你也可以通过 SANDBOX_FILES_DIR 环境变量自定义保存位置。
    代码中创建的文件会保存在 /workspace 目录下。

    Args:
        container_id: 沙箱容器的 ID。
        code: 要执行的 Python 代码。
        dependencies: 运行前要安装的 pip 包列表（例如 ['numpy', 'pandas']）。
    """
    output_log = []

    try:
        # 1. 如果请求，安装依赖项
        if dependencies:
            output_log.append(f"Installing dependencies: {dependencies}...")
            docker_utils.ensure_dependencies(container_id, dependencies)
            output_log.append("Dependencies installed.")

        # 2. 执行代码
        output_log.append("Executing Python code...")
        stdout, stderr = docker_utils.run_python_code(container_id, code)

        result = "--- Execution Result ---\n"
        if stdout:
            result += f"STDOUT:\n{stdout}\n"
        if stderr:
            result += f"STDERR:\n{stderr}\n"
        if not stdout and not stderr:
            result += "(No output)\n"

        output_log.append(result)
        return "\n".join(output_log)

    except Exception as e:
        return f"Error executing Python code: {str(e)}"


@mcp.tool()
async def run_python_ephemeral(
    code: str,
    dependencies: List[str] = Field(default_factory=list),
    image: str = "python:3.11-slim",
) -> List[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """
    在临时容器中运行一次性 Python 脚本。
    返回控制台输出和工作区中创建的任何文件。

    文件默认会持久化到宿主机的临时目录：
    - Windows: %TEMP%/python-sandbox-mcp/files/
    - macOS/Linux: /tmp/python-sandbox-mcp/files/

    你也可以通过 SANDBOX_FILES_DIR 环境变量自定义保存位置，
    或设置 SANDBOX_FILES_DIR="" 来禁用持久化。

    代码中创建的文件保存在 /workspace 目录下，会被自动检测并返回。

    Args:
        code: 要执行的 Python 代码。
        dependencies: 要安装的 pip 包列表。
        image: 要使用的 Docker 镜像。
    """
    container_id = None
    try:
        # 1. 启动沙箱
        if not docker_utils.is_docker_running():
            return [
                types.TextContent(type="text", text="Error: Docker is not running.")
            ]

        container_id = docker_utils.start_sandbox(image=image)

        console_output = ""

        # 2. 安装依赖项
        if dependencies:
            docker_utils.ensure_dependencies(container_id, dependencies)

        # 3. 运行代码
        stdout, stderr = docker_utils.run_python_code(container_id, code)

        console_output += "--- STDOUT ---\n" + stdout + "\n"
        if stderr:
            console_output += "--- STDERR ---\n" + stderr + "\n"

        # 4. 收集文件
        content_list: List[
            Union[types.TextContent, types.ImageContent, types.EmbeddedResource]
        ] = []
        content_list.append(types.TextContent(type="text", text=console_output))

        files = docker_utils.list_files(container_id)
        for rel_path in files:
            # 跳过特定目录
            if "pycache" in rel_path or rel_path.startswith("."):
                continue

            file_data = docker_utils.read_file(container_id, f"/workspace/{rel_path}")

            # 确定类型
            lower_name = rel_path.lower()
            if lower_name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                # 图像
                b64_data = base64.b64encode(file_data).decode("utf-8")
                # Determine mime type
                ext = lower_name.split(".")[-1]
                mime_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"
                content_list.append(
                    types.ImageContent(
                        type="image",
                        data=b64_data,
                        mimeType=mime_type,
                    )
                )
            else:
                # 为了简化此 MVP，视为文本
                try:
                    text_content = file_data.decode("utf-8")
                    content_list.append(
                        types.TextContent(
                            type="text",
                            text=f"--- File: {rel_path} ---\n{text_content}\n",
                        )
                    )
                except UnicodeDecodeError:
                    content_list.append(
                        types.TextContent(
                            type="text",
                            text=(
                                f"--- File: {rel_path} "
                                f"(Binary content, {len(file_data)} bytes) ---\n"
                            ),
                        )
                    )

        return content_list

    except Exception as e:
        return [
            types.TextContent(
                type="text", text=f"Error during ephemeral execution: {str(e)}"
            )
        ]

    finally:
        # 5. 清理
        if container_id:
            try:
                docker_utils.stop_sandbox(container_id)
            except Exception as e:
                logger.error(f"Failed to stop ephemeral container {container_id}: {e}")


@mcp.tool()
async def search_pypi_packages(query: str) -> str:
    """
    Search for Python packages on PyPI (scraping pypi.org).

    Args:
        query: The search term (e.g. "pandas", "data analysis").
    """
    url = "https://pypi.org/search/"
    params = {"q": query}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, follow_redirects=True)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        snippets = soup.find_all("a", class_="package-snippet")

        output = []
        if snippets:
            for snippet in snippets[:5]:  # Top 5
                name_elem = snippet.find("span", class_="package-snippet__name")
                version_elem = snippet.find("span", class_="package-snippet__version")
                desc_elem = snippet.find("p", class_="package-snippet__description")

                name = name_elem.text.strip() if name_elem else "Unknown"
                version = version_elem.text.strip() if version_elem else "?"
                desc = desc_elem.text.strip() if desc_elem else "No description"

                output.append(f"- **{name}** ({version}): {desc}")

        # Fallback to JSON API for exact match if search fails
        # (common for single package lookup)
        if not output:
            json_url = f"https://pypi.org/pypi/{query}/json"
            async with httpx.AsyncClient(headers=headers) as client:
                json_resp = await client.get(json_url, follow_redirects=True)

            if json_resp.status_code == 200:
                data = json_resp.json()
                info = data.get("info", {})
                name = info.get("name", query)
                version = info.get("version", "?")
                summary = info.get("summary", "No summary")
                output.append(f"- **{name}** ({version}): {summary} (Exact Match)")

        if not output:
            return f"No packages found for '{query}'."

        return "\n".join(output)

    except Exception as e:
        return f"Error searching PyPI: {str(e)}"


@mcp.tool()
async def sandbox_stop(container_id: str) -> str:
    """
    终止并移除正在运行的沙箱容器。

    Args:
        container_id: 要停止的沙箱容器的 ID。
    """
    try:
        docker_utils.stop_sandbox(container_id)
        return f"Sandbox {container_id} stopped and removed."
    except Exception as e:
        return f"Failed to stop sandbox: {str(e)}"


def start_cleanup_thread(interval_seconds: int = 600):
    """
    后台线程定期清理过期容器。
    """

    def loop():
        while True:
            try:
                docker_utils.cleanup_old_containers()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
            time.sleep(interval_seconds)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    logger.info("Cleanup thread started.")


def main():
    # 启动后台清理器
    start_cleanup_thread()
    # 运行 MCP 服务器
    mcp.run()


if __name__ == "__main__":
    main()
