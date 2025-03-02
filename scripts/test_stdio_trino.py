#!/usr/bin/env python3
"""
Test script for the Trino MCP protocol using STDIO transport.
This avoids the SSE transport issues we're encountering.
"""
import json
import os
import subprocess
import sys
import time
from typing import Dict, Any, Optional, List

def test_mcp_stdio():
    """
    Test the MCP protocol using a subprocess with STDIO transport.
    """
    print("🚀 Testing Trino MCP with STDIO transport...")
    
    # Start the MCP server in a subprocess with STDIO transport
    print("Starting MCP server with STDIO transport...")
    mcp_server_cmd = [
        "docker", "exec", "-it", "trino_mcp_trino-mcp_1", 
        "python", "-m", "trino_mcp.server", "--transport", "stdio"
    ]
    
    process = subprocess.Popen(
        mcp_server_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )
    
    # Helper function to send a request and get a response
    def send_request(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        request_str = json.dumps(request) + "\n"
        print(f"\n📤 Sending: {request_str.strip()}")
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # Read response with timeout
        start_time = time.time()
        timeout = 10  # 10 seconds timeout
        response_str = None
        
        while time.time() - start_time < timeout:
            response_str = process.stdout.readline().strip()
            if response_str:
                print(f"📩 Received: {response_str}")
                try:
                    return json.loads(response_str)
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing response as JSON: {e}")
            time.sleep(0.1)
            
        print("⏱️ Timeout waiting for response")
        return None
    
    # Read any startup output to clear the buffer
    print("Waiting for server startup...")
    time.sleep(2)  # Give the server time to start up
    
    # Initialize the protocol
    print("\n=== Step 1: Initialize MCP ===")
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "trino-mcp-test-client",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": True,
                "resources": {
                    "supportedSources": ["trino://catalog"]
                }
            }
        }
    }
    
    initialize_response = send_request(initialize_request)
    if not initialize_response:
        print("❌ Failed to initialize MCP")
        process.terminate()
        return
    
    print("✅ MCP initialized successfully")
    print(f"Server info: {json.dumps(initialize_response.get('result', {}).get('serverInfo', {}), indent=2)}")
    
    # Send initialized notification
    print("\n=== Step 2: Send initialized notification ===")
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "initialized"
    }
    
    _ = send_request(initialized_notification)
    print("✅ Initialized notification sent")
    
    # Get available tools
    print("\n=== Step 3: List available tools ===")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }
    
    tools_response = send_request(tools_request)
    if not tools_response or "result" not in tools_response:
        print("❌ Failed to get tools list")
        process.terminate()
        return
    
    tools = tools_response.get("result", {}).get("tools", [])
    print(f"✅ Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.get('name')}: {tool.get('description')}")
    
    # Execute a simple query
    print("\n=== Step 4: Execute a query ===")
    query_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "execute_query",
            "arguments": {
                "sql": "SELECT * FROM memory.bullshit.bullshit_data",
                "catalog": "memory"
            }
        }
    }
    
    query_response = send_request(query_request)
    if not query_response:
        print("❌ Failed to execute query")
    elif "error" in query_response:
        print(f"❌ Query error: {query_response.get('error')}")
    else:
        result = query_response.get("result", {})
        row_count = result.get("row_count", 0)
        print(f"✅ Query executed successfully with {row_count} rows")
        
        # Print columns and preview rows
        print(f"Columns: {', '.join(result.get('columns', []))}")
        print("Preview rows:")
        for row in result.get("preview_rows", []):
            print(f"  {row}")
    
    # Execute a summary query
    print("\n=== Step 5: Query the summary view ===")
    summary_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "execute_query",
            "arguments": {
                "sql": "SELECT * FROM memory.bullshit.bullshit_summary ORDER BY count DESC",
                "catalog": "memory"
            }
        }
    }
    
    summary_response = send_request(summary_request)
    if not summary_response:
        print("❌ Failed to execute summary query")
    elif "error" in summary_response:
        print(f"❌ Summary query error: {summary_response.get('error')}")
    else:
        result = summary_response.get("result", {})
        row_count = result.get("row_count", 0)
        print(f"✅ Summary query executed successfully with {row_count} rows")
        
        # Print columns and preview rows
        print(f"Columns: {', '.join(result.get('columns', []))}")
        print("Summary data:")
        for row in result.get("preview_rows", []):
            print(f"  {row}")
    
    # List available resources
    print("\n=== Step 6: List available resources ===")
    resources_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "resources/list",
        "params": {
            "source": "trino://catalog"
        }
    }
    
    resources_response = send_request(resources_request)
    if not resources_response or "result" not in resources_response:
        print("❌ Failed to get resources list")
    else:
        resources = resources_response.get("result", {}).get("resources", [])
        print(f"✅ Available resources: {len(resources)}")
        for resource in resources:
            print(f"  - {resource}")
    
    # Clean up the process
    print("\n=== Finishing test ===")
    process.terminate()
    try:
        process.wait(timeout=5)
        print("✅ MCP server process terminated")
    except subprocess.TimeoutExpired:
        print("⚠️ Had to force kill the MCP server process")
        process.kill()
    
    # Check for errors in stderr
    stderr = process.stderr.read()
    if stderr:
        print("\n⚠️ Server stderr output:")
        print(stderr)
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    test_mcp_stdio() 