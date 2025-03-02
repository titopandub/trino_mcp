#!/usr/bin/env python3
"""
Minimalist MCP STDIO test to run inside the container.
This script avoids importing any external modules and uses just the Python standard library.
"""
import json
import subprocess
import time
import sys
import threading

def test_mcp_stdio():
    """Run a test of the MCP server using STDIO transport inside the container."""
    print("🚀 Testing MCP with STDIO transport (container version)")
    
    # Start the MCP server with STDIO transport
    # We're directly using the module since we're in the container
    # Explicitly set the Trino host to trino:8080
    server_cmd = [
        "python", "-m", "trino_mcp.server", 
        "--transport", "stdio", 
        "--debug",
        "--trino-host", "trino",
        "--trino-port", "8080",
        "--trino-catalog", "memory"
    ]
    
    try:
        # Start the server in a subprocess
        process = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Set up a thread to monitor stderr and print it
        def print_stderr():
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                print(f"🔴 SERVER ERROR: {line.strip()}")
                
        stderr_thread = threading.Thread(target=print_stderr, daemon=True)
        stderr_thread.start()
        
        print("Starting server process...")
        # Sleep to allow server to initialize
        time.sleep(2)

        # Helper function to send a request and get a response
        def send_request(request_data, request_desc="", expect_response=True):
            request_json = json.dumps(request_data) + "\n"
            print(f"\n📤 Sending {request_desc}: {request_json.strip()}")
            
            try:
                process.stdin.write(request_json)
                process.stdin.flush()
            except BrokenPipeError:
                print(f"❌ Broken pipe when sending {request_desc}")
                return None
                
            # If we don't expect a response (notification), just return
            if not expect_response:
                print(f"✅ Sent {request_desc} (no response expected)")
                return True
            
            # Read response with timeout
            print(f"Waiting for {request_desc} response...")
            start_time = time.time()
            timeout = 10
            
            while time.time() - start_time < timeout:
                # Check if process is still running
                if process.poll() is not None:
                    print(f"Server process exited with code {process.returncode}")
                    return None
                
                # Try to read a line from stdout
                response_line = process.stdout.readline().strip()
                if response_line:
                    print(f"📩 Received response: {response_line}")
                    try:
                        return json.loads(response_line)
                    except json.JSONDecodeError as e:
                        print(f"❌ Error parsing response: {e}")
                
                # Wait a bit before trying again
                time.sleep(0.1)
            
            print(f"⏱️ Timeout waiting for {request_desc} response")
            return None
        
        # STEP 1: Initialize the server
        print("\n=== STEP 1: Initialize Server ===")
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05", 
                "clientInfo": {
                    "name": "container-stdio-test",
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
        
        init_response = send_request(initialize_request, "initialize request")
        if not init_response:
            raise Exception("Failed to initialize MCP server")

        server_info = init_response.get("result", {}).get("serverInfo", {})
        print(f"✅ Connected to server: {server_info.get('name')} {server_info.get('version')}")
        
        # STEP 2: Send initialized notification (no response expected)
        print("\n=== STEP 2: Send Initialized Notification ===")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}  # Empty params object is required
        }
        _ = send_request(initialized_notification, "initialized notification", expect_response=False)
        
        # STEP 3: List available tools
        print("\n=== STEP 3: List Available Tools ===")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        tools_response = send_request(tools_request, "tools list request")
        if not tools_response:
            print("❌ Failed to list tools")
        else:
            tools = tools_response.get("result", {}).get("tools", [])
            print(f"✅ Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
        
        # STEP 4: Execute a simple query
        if tools_response:
            print("\n=== STEP 4: Execute Simple Query ===")
            query_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "execute_query",
                    "arguments": {
                        "sql": "SELECT 'Hello, world!' AS greeting",
                        "catalog": "memory"
                    }
                }
            }
            
            query_response = send_request(query_request, "query execution")
            if not query_response:
                print("❌ Failed to execute query")
            elif "error" in query_response:
                print(f"❌ Query error: {json.dumps(query_response.get('error', {}), indent=2)}")
            else:
                result = query_response.get("result", {})
                print(f"✅ Query executed successfully:")
                print(f"  Columns: {', '.join(result.get('columns', []))}")
                print(f"  Row count: {result.get('row_count', 0)}")
                print(f"  Preview rows: {json.dumps(result.get('preview_rows', []), indent=2)}")
        
            # STEP 5: Try to query a bullshit table
            print("\n=== STEP 5: Query Bullshit Table ===")
            bs_query_request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "execute_query",
                    "arguments": {
                        "sql": "SELECT * FROM memory.bullshit.bullshit_data LIMIT 3",
                        "catalog": "memory"
                    }
                }
            }
            
            bs_query_response = send_request(bs_query_request, "bullshit table query")
            if not bs_query_response:
                print("❌ Failed to execute bullshit table query")
            elif "error" in bs_query_response:
                print(f"❌ Query error: {json.dumps(bs_query_response.get('error', {}), indent=2)}")
            else:
                result = bs_query_response.get("result", {})
                print(f"✅ Bullshit query executed successfully:")
                print(f"  Columns: {', '.join(result.get('columns', []))}")
                print(f"  Row count: {result.get('row_count', 0)}")
                print(f"  Preview rows: {json.dumps(result.get('preview_rows', []), indent=2)}")
        
        # STEP 6: Try resources listing
        print("\n=== STEP 6: List Resources ===")
        resources_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/list",
            "params": {
                "source": "trino://catalog"
            }
        }
        
        resources_response = send_request(resources_request, "resources list request")
        if not resources_response:
            print("❌ Failed to list resources")
        elif "error" in resources_response:
            print(f"❌ Resources error: {json.dumps(resources_response.get('error', {}), indent=2)}")
        else:
            resources = resources_response.get("result", {}).get("items", [])
            print(f"✅ Available resources: {len(resources)}")
            for resource in resources:
                print(f"  - {resource.get('source')}: {resource.get('path')}")
        
        # STEP 7: Shutdown
        print("\n=== STEP 7: Shutdown ===")
        shutdown_request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "shutdown"
        }
        
        shutdown_response = send_request(shutdown_request, "shutdown request")
        print("✅ Server shutdown request sent")
        
        # Send exit notification (no response expected)
        exit_notification = {
            "jsonrpc": "2.0",
            "method": "exit",
            "params": {}  # Empty params may be needed
        }
        
        _ = send_request(exit_notification, "exit notification", expect_response=False)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Make sure to terminate the process
        if 'process' in locals() and process.poll() is None:
            print("Terminating server process...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Process didn't terminate, killing it...")
                process.kill()
        
        print("\n🏁 Test completed!")

if __name__ == "__main__":
    test_mcp_stdio() 