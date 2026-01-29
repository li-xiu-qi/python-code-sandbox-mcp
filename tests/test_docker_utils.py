import pytest
from unittest.mock import MagicMock, patch
from python_code_sandbox_mcp.docker_utils import is_docker_running, start_sandbox, exec_command

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
