import docker
from docker.errors import NotFound, APIError
import logging
import uuid
import time
import os
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Configuration via Environment Variables
# For Docker Registry: Users can provide a HOST path to persist pip cache
PIP_CACHE_PATH = os.getenv("PIP_CACHE_PATH")
ENABLE_PIP_CACHE = os.getenv("ENABLE_PIP_CACHE", "true").lower() == "true"

# Resource Limits
SANDBOX_MEMORY_LIMIT = os.getenv("SANDBOX_MEMORY_LIMIT", "2g")
SANDBOX_CPU_PERIOD = int(os.getenv("SANDBOX_CPU_PERIOD", "100000"))
SANDBOX_CPU_QUOTA = int(os.getenv("SANDBOX_CPU_QUOTA", "50000"))

# Registry to track active containers and their creation time
active_sandboxes: Dict[str, float] = {}


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


def start_sandbox(image: str = "python:3.11-slim", timeout_seconds: int = 300) -> str:
    """
    Start a new Python sandbox container.
    """
    client = get_docker_client()

    run_id = str(uuid.uuid4())[:8]
    container_name = f"py-sbx-{run_id}"

    try:
        logger.info(f"Starting sandbox container {container_name} with image {image}")

        # Configure volumes for pip cache if enabled and path is provided
        volumes = {}
        if ENABLE_PIP_CACHE and PIP_CACHE_PATH:
            # We mount the provided host path to the standard pip cache location in the container
            volumes[PIP_CACHE_PATH] = {"bind": "/root/.cache/pip", "mode": "rw"}

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

    import base64

    b64_code = base64.b64encode(code.encode("utf-8")).decode("utf-8")

    # 一次性解码并运行
    cmd = f"python -c \"import base64; exec(base64.b64decode('{b64_code}').decode('utf-8'))\""

    exit_code, stdout, stderr = exec_command(container_id, cmd)

    return stdout, stderr


def list_files(container_id: str, path: str = "/workspace") -> List[str]:
    """
    列出容器内指定目录下的文件。
    """
    # ls -p 会给目录添加 /。grep -v / 会过滤掉它们。
    cmd = f"ls -p {path} | grep -v /"
    exit_code, stdout, stderr = exec_command(container_id, cmd)
    if exit_code != 0:
        return []
    return [f.strip() for f in stdout.split("\n") if f.strip()]


def read_file(container_id: str, filepath: str) -> bytes:
    """
    Read file content from container. Returns bytes.
    """
    import base64

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
