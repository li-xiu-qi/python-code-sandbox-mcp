import os
from unittest.mock import patch
import importlib
import python_code_sandbox_mcp.docker_utils as docker_utils


def test_config_loading_from_env():
    """验证程序能正确读取环境变量（模拟 .env 的作用）"""
    with patch.dict(os.environ, {
        "PIP_CACHE_PATH": "/tmp/fake-cache",
        "ENABLE_PIP_CACHE": "false",
        "SANDBOX_MEMORY_LIMIT": "4g",
        "SANDBOX_FILES_DIR": "/custom/files/dir"
    }):
        # 重置 _current_files_dir 以便重新加载
        docker_utils._current_files_dir = None
        
        # 重新加载模块以应用新的环境变量
        importlib.reload(docker_utils)
        
        assert docker_utils.PIP_CACHE_PATH == "/tmp/fake-cache"
        assert docker_utils.ENABLE_PIP_CACHE is False
        assert docker_utils.SANDBOX_MEMORY_LIMIT == "4g"
        assert docker_utils.SANDBOX_FILES_DIR == "/custom/files/dir"


def test_config_default_values():
    """验证在没有环境变量时，程序使用正确的默认值"""
    with patch.dict(os.environ, {}, clear=True):
        # 重置 _current_files_dir 以便重新加载
        docker_utils._current_files_dir = None
        
        importlib.reload(docker_utils)
        
        assert docker_utils.PIP_CACHE_PATH is None
        assert docker_utils.ENABLE_PIP_CACHE is True  # 默认开启
        assert docker_utils.SANDBOX_MEMORY_LIMIT == "2g"
        assert docker_utils.SANDBOX_FILES_DIR is None  # 默认未设置


def test_sandbox_files_dir_empty_string_disables_persistence():
    """验证设置 SANDBOX_FILES_DIR='' 会禁用文件持久化"""
    with patch.dict(os.environ, {
        "SANDBOX_FILES_DIR": ""  # 空字符串表示禁用
    }):
        # 重置 _current_files_dir 以便重新加载
        docker_utils._current_files_dir = None
        
        importlib.reload(docker_utils)
        
        # 空字符串表示禁用持久化
        assert docker_utils.SANDBOX_FILES_DIR == ""
        
        # get_files_dir 应该返回 None
        result = docker_utils.get_files_dir()
        assert result is None


def test_sandbox_files_dir_custom_path():
    """验证自定义 SANDBOX_FILES_DIR 路径会被使用"""
    custom_path = "/my/custom/sandbox/files"
    
    with patch.dict(os.environ, {
        "SANDBOX_FILES_DIR": custom_path
    }):
        # 重置 _current_files_dir 以便重新加载
        docker_utils._current_files_dir = None
        
        importlib.reload(docker_utils)
        
        # 应该使用用户指定的路径
        result = docker_utils.get_files_dir()
        assert result == custom_path


def test_sandbox_files_dir_auto_default():
    """验证未设置 SANDBOX_FILES_DIR 时使用系统临时目录"""
    with patch.dict(os.environ, {}, clear=True):
        # 重置 _current_files_dir 以便重新加载
        docker_utils._current_files_dir = None
        
        importlib.reload(docker_utils)
        
        # 应该使用系统临时目录
        result = docker_utils.get_files_dir()
        assert result is not None
        assert "python-sandbox-mcp" in result
        assert "files" in result
