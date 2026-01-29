import os
from unittest.mock import patch
import importlib
import python_code_sandbox_mcp.docker_utils as docker_utils

def test_config_loading_from_env():
    """验证程序能正确读取环境变量（模拟 .env 的作用）"""
    with patch.dict(os.environ, {
        "PIP_CACHE_PATH": "/tmp/fake-cache",
        "ENABLE_PIP_CACHE": "false",
        "SANDBOX_MEMORY_LIMIT": "4g"
    }):
        # 重新加载模块以应用新的环境变量
        importlib.reload(docker_utils)
        
        assert docker_utils.PIP_CACHE_PATH == "/tmp/fake-cache"
        assert docker_utils.ENABLE_PIP_CACHE is False
        assert docker_utils.SANDBOX_MEMORY_LIMIT == "4g"

def test_config_default_values():
    """验证在没有环境变量时，程序使用正确的默认值"""
    with patch.dict(os.environ, {}, clear=True):
        importlib.reload(docker_utils)
        
        assert docker_utils.PIP_CACHE_PATH is None
        assert docker_utils.ENABLE_PIP_CACHE is True  # 默认开启
        assert docker_utils.SANDBOX_MEMORY_LIMIT == "2g"
