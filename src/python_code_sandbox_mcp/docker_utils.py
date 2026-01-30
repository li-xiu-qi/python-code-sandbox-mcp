import base64
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import docker
from docker.errors import APIError, NotFound

logger = logging.getLogger(__name__)

# Configuration via Environment Variables
# For Docker Registry: Users can provide a HOST path to persist pip cache
PIP_CACHE_PATH = os.getenv("PIP_CACHE_PATH")
ENABLE_PIP_CACHE = os.getenv("ENABLE_PIP_CACHE", "true").lower() == "true"

# Host path for persistent files
# Priority: SANDBOX_FILES_DIR > Auto temp dir > None (no persistence)
SANDBOX_FILES_DIR = os.getenv("SANDBOX_FILES_DIR")

# Resource Limits
SANDBOX_MEMORY_LIMIT = os.getenv("SANDBOX_MEMORY_LIMIT", "2g")
SANDBOX_CPU_PERIOD = int(os.getenv("SANDBOX_CPU_PERIOD", "100000"))
SANDBOX_CPU_QUOTA = int(os.getenv("SANDBOX_CPU_QUOTA", "50000"))

# Registry to track active containers and their creation time
active_sandboxes: Dict[str, float] = {}

# Track the actual files directory being used (for retrieval)
_current_files_dir: Optional[str] = None


def get_docker_client():
    try:
        return docker.from_env()
    except Exception as e:
        logger.error(f"Failed to connect to Docker daemon: {e}")
        raise RuntimeError(
            "Docker is not running or accessible. Please ensure Docker Desktop is started."
        )


def is_docker_running() -> bool:
    try:
        client = get_docker_client()
        client.ping()
        return True
    except Exception:
        return False


def get_files_dir() -> Optional[str]:
    """
    获取用于持久化文件的宿主机目录。

    优先级：
    1. SANDBOX_FILES_DIR 环境变量（如果设置为空字符串，则禁用持久化）
    2. 系统自动创建的临时目录（智能默认）

    Returns:
        宿主机目录路径，如果禁用持久化则返回 None
    """
    global _current_files_dir

    # 如果已经确定，直接返回
    if _current_files_dir is not None:
        return _current_files_dir if _current_files_dir else None

    # 1. 检查环境变量
    env_value = os.getenv("SANDBOX_FILES_DIR")

    if env_value is not None:
        # 用户明确设置了（即使是空字符串）
        if env_value == "":
            # 空字符串表示禁用持久化
            _current_files_dir = ""
            logger.info("File persistence disabled (SANDBOX_FILES_DIR='')")
            return None
        else:
            # 使用用户指定的路径
            _current_files_dir = env_value
            logger.info(f"Using user-specified files directory: {_current_files_dir}")
            return _current_files_dir

    # 2. 智能默认：使用系统临时目录
    tmp_dir = Path(tempfile.gettempdir()) / "python-sandbox-mcp" / "files"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    _current_files_dir = str(tmp_dir)

    logger.info(f"Using default temp files directory: {_current_files_dir}")
    logger.info(f"Files will be persisted to: {_current_files_dir}")

    return _current_files_dir


def reset_files_dir():
    """重置文件目录（主要用于测试）"""
    global _current_files_dir
    _current_files_dir = None


def start_sandbox(image: str = "python:3.11-slim", timeout_seconds: int = 300) -> str:
    """
    Start a new Python sandbox container.
    """
    client = get_docker_client()

    run_id = str(uuid.uuid4())[:8]
    container_name = f"py-sbx-{run_id}"

    try:
        logger.info(f"Starting sandbox container {container_name} with image {image}")

        # Configure volumes
        volumes = {}

        # 1. Pip cache
        if ENABLE_PIP_CACHE and PIP_CACHE_PATH:
            # We mount the provided host path to the standard pip cache location in the container
            volumes[PIP_CACHE_PATH] = {"bind": "/root/.cache/pip", "mode": "rw"}

        # 2. Persistent files (智能默认)
        files_dir = get_files_dir()
        if files_dir:
            # Ensure the directory exists on host
            os.makedirs(files_dir, exist_ok=True)
            # 挂载到容器的 /workspace 目录
            volumes[files_dir] = {"bind": "/workspace", "mode": "rw"}
            logger.info(f"Mounted {files_dir} to /workspace for file persistence")

        container = client.containers.run(
            image,
            command="tail -f /dev/null",
            name=container_name,
            detach=True,
            labels={"mcp_sandbox": "true", "run_id": run_id},
            working_dir="/workspace",
            volumes=volumes,
            mem_limit=SANDBOX_MEMORY_LIMIT,
            cpu_period=SANDBOX_CPU_PERIOD,
            cpu_quota=SANDBOX_CPU_QUOTA,
        )

        container_id = container.id
        active_sandboxes[container_id] = time.time()
        return container_id

    except APIError as e:
        logger.error(f"Docker API Error: {e}")
        raise RuntimeError(f"Failed to start sandbox: {e}")


def stop_sandbox(container_id: str):
    """
    Stop and remove a sandbox container.
    """
    client = get_docker_client()
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=1)
        container.remove()
        if container_id in active_sandboxes:
            del active_sandboxes[container_id]
        logger.info(f"Stopped sandbox {container_id}")
    except NotFound:
        pass
    except Exception as e:
        logger.error(f"Error stopping sandbox {container_id}: {e}")
        raise


def exec_command(container_id: str, command: str) -> Tuple[int, str, str]:
    """
    Execute a shell command in the container.
    """
    client = get_docker_client()
    try:
        container = client.containers.get(container_id)
        exec_result = container.exec_run(cmd=["/bin/sh", "-c", command], demux=True)

        exit_code = exec_result.exit_code
        stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""

        return exit_code, stdout, stderr

    except NotFound:
        raise ValueError(f"Container {container_id} not found.")
    except Exception as e:
        raise RuntimeError(f"Exec failed: {e}")


def ensure_dependencies(container_id: str, packages: List[str]) -> str:
    """
    Ensure specific pip packages are installed.
    """
    if not packages:
        return ""

    logger.info(f"Installing dependencies in {container_id}: {packages}")
    pkg_str = " ".join(packages)

    # Use pip to install.
    # We only use --no-cache-dir if cache is explicitly disabled
    cache_flag = "--no-cache-dir" if not ENABLE_PIP_CACHE else ""
    cmd = f"pip install {cache_flag} --disable-pip-version-check {pkg_str}"

    exit_code, stdout, stderr = exec_command(container_id, cmd)

    if exit_code != 0:
        raise RuntimeError(f"Failed to install dependencies: {stderr}")

    return stdout


def run_python_code(container_id: str, code: str) -> Tuple[str, str]:
    """
    在容器中运行 Python 代码。
    返回 (stdout, stderr)。
    """
    # 1. 将代码写入容器内的文件
    # 目前我们使用简单的 echo 方法，或者我们可以使用 docker cp。
    # 对于健壮的多行字符串，我们可能需要比简单的 echo 更好的方法。
    # 但是通过 python 单行命令写入临时文件在转义方面更安全。

    b64_code = base64.b64encode(code.encode("utf-8")).decode("utf-8")

    # 一次性解码并运行
    cmd = f"python -c \"import base64; exec(base64.b64decode('{b64_code}').decode('utf-8'))\""

    exit_code, stdout, stderr = exec_command(container_id, cmd)

    return stdout, stderr


def list_files(container_id: str, path: str = "/workspace") -> List[str]:
    """
    列出容器内指定目录下的文件。
    返回文件的相对路径。
    """
    # -F adds / to directories, -R is recursive
    # We want to find all files but ignore some directories like __pycache__
    cmd = f"find {path} -maxdepth 2 -not -path '*/.*' -type f"
    exit_code, stdout, stderr = exec_command(container_id, cmd)
    if exit_code != 0:
        return []

    files = []
    for f in stdout.split("\n"):
        f = f.strip()
        if not f:
            continue
        # Convert absolute path to relative path from /workspace
        rel_path = os.path.relpath(f, "/workspace")
        if rel_path.startswith(".."):
            continue
        files.append(rel_path)
    return files


def read_file(container_id: str, filepath: str) -> bytes:
    """
    Read file content from container. Returns bytes.
    """
    # Use base64 inside the container to safely cat binary files
    # Quote the filepath to handle spaces
    cmd = f"cat '{filepath}' | base64"
    exit_code, stdout, stderr = exec_command(container_id, cmd)

    if exit_code != 0:
        raise RuntimeError(f"Failed to read file {filepath}: {stderr}")

    try:
        # 输出是 base64 字符串，我们需要解码它以获取原始字节
        # 移除 base64 命令可能添加的换行符
        clean_b64 = stdout.replace("\n", "").strip()
        return base64.b64decode(clean_b64)
    except Exception as e:
        raise RuntimeError(f"Failed to decode file {filepath}: {e}")


def read_file_from_host(filename: str) -> Optional[bytes]:
    """
    从宿主机的持久化目录读取文件。
    用于在容器销毁后获取文件。

    Args:
        filename: 文件名（相对路径）

    Returns:
        文件内容，如果文件不存在或持久化未启用则返回 None
    """
    files_dir = get_files_dir()
    if not files_dir:
        return None

    file_path = Path(files_dir) / filename
    if not file_path.exists():
        return None

    return file_path.read_bytes()


def list_host_files() -> List[str]:
    """
    列出宿主机持久化目录中的所有文件。

    Returns:
        文件名列表
    """
    files_dir = get_files_dir()
    if not files_dir:
        return []

    path = Path(files_dir)
    if not path.exists():
        return []

    return [f.name for f in path.iterdir() if f.is_file()]


def cleanup_old_containers(max_age_seconds: int = 3600):
    """
    定期调用的清理函数。
    """
    get_docker_client()
    now = time.time()

    to_remove = []
    for cid, start_time in active_sandboxes.items():
        if now - start_time > max_age_seconds:
            to_remove.append(cid)

    for cid in to_remove:
        logger.info(f"Container {cid} expired, cleaning up.")
        try:
            stop_sandbox(cid)
        except Exception:
            pass
