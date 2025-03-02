"""
Pytest configuration for the Trino MCP server tests.
"""

import os
import time
import json
import pytest
import requests
import subprocess
import signal
from typing import Dict, Any, Iterator, Tuple

# Define constants
TEST_SERVER_PORT = 7000  # Using port 7000 to avoid ALL conflicts with existing containers
TEST_SERVER_URL = f"http://localhost:{TEST_SERVER_PORT}"
TRINO_HOST = os.environ.get("TEST_TRINO_HOST", "localhost")
TRINO_PORT = int(os.environ.get("TEST_TRINO_PORT", "9095"))
TRINO_USER = os.environ.get("TEST_TRINO_USER", "trino")


class TrinoMCPTestServer:
    """Helper class to manage a test instance of the Trino MCP server."""
    
    def __init__(self, port: int = TEST_SERVER_PORT):
        self.port = port
        self.process = None
        
    def start(self) -> None:
        """Start the server process."""
        cmd = [
            "python", "-m", "trino_mcp.server",
            "--transport", "sse",
            "--port", str(self.port),
            "--trino-host", TRINO_HOST,
            "--trino-port", str(TRINO_PORT),
            "--trino-user", TRINO_USER,
            "--trino-catalog", "memory",
            "--debug"
        ]
        
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        self._wait_for_server()
        
    def stop(self) -> None:
        """Stop the server process."""
        if self.process:
            self.process.send_signal(signal.SIGINT)
            self.process.wait()
            self.process = None
            
    def _wait_for_server(self, max_retries: int = 10, retry_interval: float = 0.5) -> None:
        """Wait for the server to become available."""
        for _ in range(max_retries):
            try:
                response = requests.get(f"{TEST_SERVER_URL}/mcp")
                if response.status_code == 200:
                    return
            except requests.exceptions.ConnectionError:
                pass
            
            time.sleep(retry_interval)
            
        raise TimeoutError(f"Server did not start within {max_retries * retry_interval} seconds")


def check_trino_available() -> bool:
    """Check if Trino server is available for testing."""
    try:
        response = requests.get(f"http://{TRINO_HOST}:{TRINO_PORT}/v1/info")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


class MCPClient:
    """Simple MCP client for testing."""
    
    def __init__(self, base_url: str = TEST_SERVER_URL):
        self.base_url = base_url
        self.next_id = 1
        self.initialized = False
        
    def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP session."""
        if self.initialized:
            return {"already_initialized": True}
            
        response = self._send_request("initialize", {
            "capabilities": {}
        })
        
        self.initialized = True
        return response
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return self._send_request("tools/list")
    
    def list_resources(self, source: str = None, path: str = None) -> Dict[str, Any]:
        """List resources."""
        params = {}
        if source:
            params["source"] = source
        if path:
            params["path"] = path
            
        return self._send_request("resources/list", params)
    
    def get_resource(self, source: str, path: str) -> Dict[str, Any]:
        """Get a specific resource."""
        return self._send_request("resources/get", {
            "source": source,
            "path": path
        })
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool with the given arguments."""
        return self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
    
    def shutdown(self) -> Dict[str, Any]:
        """Shutdown the MCP session."""
        response = self._send_request("shutdown")
        self.initialized = False
        return response
    
    def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server."""
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": method
        }
        
        if params is not None:
            request["params"] = params
            
        self.next_id += 1
        
        response = requests.post(
            f"{self.base_url}/mcp/message",
            json=request
        )
        
        if response.status_code != 200:
            raise Exception(f"Request failed with status {response.status_code}: {response.text}")
            
        return response.json()


@pytest.fixture(scope="session")
def trino_available() -> bool:
    """Check if Trino is available."""
    available = check_trino_available()
    if not available:
        pytest.skip("Trino server is not available for testing")
    return available


@pytest.fixture(scope="session")
def mcp_server(trino_available) -> Iterator[None]:
    """
    Start a test instance of the Trino MCP server for the test session.
    
    Args:
        trino_available: Fixture to ensure Trino is available.
        
    Yields:
        None
    """
    server = TrinoMCPTestServer()
    try:
        server.start()
        yield
    finally:
        server.stop()


@pytest.fixture
def mcp_client(mcp_server) -> Iterator[MCPClient]:
    """
    Create a test MCP client connected to the test server.
    
    Args:
        mcp_server: The server fixture.
        
    Yields:
        MCPClient: An initialized MCP client.
    """
    client = MCPClient()
    client.initialize()
    try:
        yield client
    finally:
        try:
            client.shutdown()
        except:
            pass  # Ignore errors during shutdown 