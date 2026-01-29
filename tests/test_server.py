import pytest
import mcp.types as types
from unittest.mock import MagicMock, patch
from python_code_sandbox_mcp.server import search_pypi_packages, run_python_ephemeral

@pytest.mark.asyncio
async def test_search_pypi_packages_fallback():
    # Test fallback to JSON API when scraping returns nothing
    with patch('httpx.AsyncClient.get') as mock_get:
        # First call (scraping) returns empty snippets
        mock_resp_scrape = MagicMock()
        mock_resp_scrape.status_code = 200
        mock_resp_scrape.text = "<html><body></body></html>"
        
        # Second call (JSON API) returns data
        mock_resp_json = MagicMock()
        mock_resp_json.status_code = 200
        mock_resp_json.json.return_value = {
            "info": {"name": "test-pkg", "version": "1.0.0", "summary": "test summary"}
        }
        
        mock_get.side_effect = [mock_resp_scrape, mock_resp_json]
        
        res = await search_pypi_packages("test-pkg")
        assert "test-pkg" in res
        assert "Exact Match" in res

@pytest.mark.asyncio
async def test_run_python_ephemeral_error_no_docker():
    with patch('python_code_sandbox_mcp.docker_utils.is_docker_running', return_value=False):
        results = await run_python_ephemeral("print(1)")
        assert len(results) == 1
        assert "Docker is not running" in results[0].text
