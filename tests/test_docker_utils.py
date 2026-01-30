import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_code_sandbox_mcp.docker_utils import (
    is_docker_running, 
    start_sandbox, 
    exec_command,
    get_files_dir,
    reset_files_dir,
    read_file_from_host,
    list_host_files
)


def test_is_docker_running_true():
    with patch('docker.from_env') as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        assert is_docker_running() is True


def test_is_docker_running_false():
    with patch('docker.from_env', side_effect=Exception("Docker not found")):
        assert is_docker_running() is False


def test_exec_command_logic():
    with patch('docker.from_env') as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        
        # Mock exec_run return value (exit_code, (stdout, stderr))
        mock_container.exec_run.return_value = MagicMock(
            exit_code=0, 
            output=(b"hello", b"")
        )
        
        exit_code, stdout, stderr = exec_command("fake-id", "echo hello")
        assert exit_code == 0
        assert stdout == "hello"


class TestGetFilesDir:
    """测试 get_files_dir 函数的三种模式"""
    
    def setup_method(self):
        """每个测试方法前重置状态"""
        reset_files_dir()
    
    def teardown_method(self):
        """每个测试方法后清理环境变量"""
        reset_files_dir()
    
    def test_get_files_dir_returns_cached_value(self):
        """测试第二次调用返回缓存值"""
        with patch.dict(os.environ, {}, clear=True):
            # 第一次调用
            result1 = get_files_dir()
            # 第二次调用应该返回相同的值
            result2 = get_files_dir()
            assert result1 == result2
    
    def test_get_files_dir_with_custom_path(self):
        """测试使用自定义路径"""
        custom_path = "/my/custom/path"
        with patch.dict(os.environ, {"SANDBOX_FILES_DIR": custom_path}):
            reset_files_dir()
            result = get_files_dir()
            assert result == custom_path
    
    def test_get_files_dir_disabled(self):
        """测试禁用持久化（空字符串）"""
        with patch.dict(os.environ, {"SANDBOX_FILES_DIR": ""}):
            reset_files_dir()
            result = get_files_dir()
            assert result is None
    
    def test_get_files_dir_auto_default(self):
        """测试自动使用系统临时目录"""
        with patch.dict(os.environ, {}, clear=True):
            reset_files_dir()
            result = get_files_dir()
            assert result is not None
            assert "python-sandbox-mcp" in result
            assert "files" in result


class TestReadFileFromHost:
    """测试从宿主机读取文件功能"""
    
    def test_read_file_from_host_success(self, tmp_path):
        """测试成功读取文件"""
        # 创建临时文件
        test_file = tmp_path / "test.txt"
        test_content = b"Hello from host!"
        test_file.write_bytes(test_content)
        
        with patch.dict(os.environ, {"SANDBOX_FILES_DIR": str(tmp_path)}):
            reset_files_dir()
            result = read_file_from_host("test.txt")
            assert result == test_content
    
    def test_read_file_from_host_not_found(self, tmp_path):
        """测试文件不存在时返回 None"""
        with patch.dict(os.environ, {"SANDBOX_FILES_DIR": str(tmp_path)}):
            reset_files_dir()
            result = read_file_from_host("nonexistent.txt")
            assert result is None
    
    def test_read_file_from_host_disabled(self):
        """测试禁用持久化时返回 None"""
        with patch.dict(os.environ, {"SANDBOX_FILES_DIR": ""}):
            reset_files_dir()
            result = read_file_from_host("test.txt")
            assert result is None


class TestListHostFiles:
    """测试列出宿主机文件功能"""
    
    def test_list_host_files_success(self, tmp_path):
        """测试成功列出文件"""
        # 创建测试文件
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()  # 目录应该被忽略
        
        with patch.dict(os.environ, {"SANDBOX_FILES_DIR": str(tmp_path)}):
            reset_files_dir()
            result = list_host_files()
            assert len(result) == 2
            assert "file1.txt" in result
            assert "file2.txt" in result
    
    def test_list_host_files_empty(self, tmp_path):
        """测试空目录返回空列表"""
        with patch.dict(os.environ, {"SANDBOX_FILES_DIR": str(tmp_path)}):
            reset_files_dir()
            result = list_host_files()
            assert result == []
    
    def test_list_host_files_disabled(self):
        """测试禁用持久化时返回空列表"""
        with patch.dict(os.environ, {"SANDBOX_FILES_DIR": ""}):
            reset_files_dir()
            result = list_host_files()
            assert result == []


class TestResetFilesDir:
    """测试 reset_files_dir 函数"""
    
    def test_reset_files_dir_clears_cache(self):
        """测试重置缓存后重新计算路径"""
        with patch.dict(os.environ, {}, clear=True):
            # 第一次调用
            result1 = get_files_dir()
            
            # 修改环境变量
            with patch.dict(os.environ, {"SANDBOX_FILES_DIR": "/new/path"}):
                # 重置缓存
                reset_files_dir()
                # 应该返回新路径
                result2 = get_files_dir()
                assert result2 == "/new/path"
                assert result1 != result2
