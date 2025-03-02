#!/usr/bin/env python3
"""
Simple test script for the Trino MCP client.
This script connects to the Trino MCP server and performs some basic operations.
"""
import json
import os
import sys
import time
import threading
from typing import Dict, Any, List, Optional, Callable

import requests
import sseclient
import logging
from rich.console import Console

# Default port for MCP server, changed to match docker-compose.yml
DEFAULT_MCP_HOST = "localhost"
DEFAULT_MCP_PORT = 9096


class SSEListener:
    """
    Server-Sent Events (SSE) listener for MCP.
    This runs in a separate thread to receive notifications from the server.
    """
    
    def __init__(self, url: str, message_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize the SSE listener.
        
        Args:
            url: The SSE endpoint URL.
            message_callback: Callback function to handle incoming messages.
        """
        self.url = url
        self.message_callback = message_callback
        self.running = False
        self.thread = None
        
    def start(self) -> None:
        """Start the SSE listener in a separate thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._listen)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self) -> None:
        """Stop the SSE listener."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
            
    def _listen(self) -> None:
        """Listen for SSE events."""
        try:
            headers = {"Accept": "text/event-stream"}
            response = requests.get(self.url, headers=headers, stream=True)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if not self.running:
                    break
                    
                try:
                    if event.data:
                        data = json.loads(event.data)
                        self.message_callback(data)
                except json.JSONDecodeError:
                    print(f"Failed to parse SSE message: {event.data}")
                except Exception as e:
                    print(f"Error processing SSE message: {e}")
                    
        except Exception as e:
            if self.running:
                print(f"SSE connection error: {e}")
        finally:
            self.running = False


def test_sse_client(base_url=f"http://localhost:{DEFAULT_MCP_PORT}"):
    """
    Test communication with the SSE transport.
    
    Args:
        base_url: The base URL of the SSE server.
    """
    print(f"Testing SSE client with {base_url}...")
    
    # First, let's check what endpoints are available
    print("Checking available endpoints...")
    try:
        response = requests.get(base_url)
        print(f"Root path status: {response.status_code}")
        if response.status_code == 200:
            print(f"Content: {response.text[:500]}")  # Print first 500 chars
    except Exception as e:
        print(f"Error checking root path: {e}")
    
    # Try common MCP endpoints
    endpoints_to_check = [
        "/mcp",
        "/mcp/sse",
        "/mcp/2024-11-05",
        "/mcp/message",
        "/api/mcp",
        "/api/mcp/sse"
    ]
    
    for endpoint in endpoints_to_check:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\nChecking endpoint: {url}")
            response = requests.get(url)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Content: {response.text[:100]}")  # Print first 100 chars
        except Exception as e:
            print(f"Error: {e}")
    
    # Try the /sse endpoint with proper SSE headers
    print("\nChecking SSE endpoint with proper headers...")
    try:
        sse_url = f"{base_url}/sse"
        print(f"Connecting to SSE endpoint: {sse_url}")
        
        # Setup SSE message handler
        def handle_sse_message(message):
            print(f"Received SSE message: {message.data}")
        
        # Use the SSEClient to connect properly
        print("Starting SSE connection...")
        headers = {"Accept": "text/event-stream"}
        response = requests.get(sse_url, headers=headers, stream=True)
        client = sseclient.SSEClient(response)
        
        # Try to get the first few events
        print("Waiting for SSE events...")
        event_count = 0
        for event in client.events():
            print(f"Event received: {event.data}")
            event_count += 1
            if event_count >= 3:  # Get at most 3 events
                break
            
    except Exception as e:
        print(f"Error with SSE connection: {e}")


if __name__ == "__main__":
    # Get the server URL from environment or command line
    server_url = os.environ.get("SERVER_URL", f"http://localhost:{DEFAULT_MCP_PORT}")
    
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
        
    test_sse_client(server_url) 