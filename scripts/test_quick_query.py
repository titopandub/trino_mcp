#!/usr/bin/env python3
"""
Quick test script that runs a single query and exits properly.
Shows that Trino works but is just empty.
"""
import json
import subprocess
import sys
import time
import threading
import os

def run_quick_query():
    """Run a quick query against Trino via MCP and exit properly."""
    print("🚀 Running quick query test - this should exit cleanly!")
    
    # Get the current directory for module path
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Start the server process with STDIO transport
    process = subprocess.Popen(
        ["python", "src/trino_mcp/server.py", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
        env=dict(os.environ, PYTHONPATH=os.path.join(current_dir, "src"))
    )
    
    # Create a thread to read stderr to prevent deadlocks
    def read_stderr():
        for line in process.stderr:
            print(f"[SERVER] {line.strip()}")
    
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_thread.start()
    
    # Wait a bit for the server to start up
    time.sleep(2)
    
    query_response = None
    try:
        # Send initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "quick-query-test", "version": "1.0.0"},
                "capabilities": {"tools": True, "resources": {"supportedSources": ["trino://catalog"]}}
            }
        }
        print(f"Sending initialize request: {json.dumps(initialize_request)}")
        process.stdin.write(json.dumps(initialize_request) + "\n")
        process.stdin.flush()
        
        # Read initialize response with timeout
        start_time = time.time()
        timeout = 5
        initialize_response = None
        
        print("Waiting for initialize response...")
        while time.time() - start_time < timeout:
            response_line = process.stdout.readline().strip()
            if response_line:
                print(f"Got response: {response_line}")
                try:
                    initialize_response = json.loads(response_line)
                    break
                except json.JSONDecodeError as e:
                    print(f"Error parsing response: {e}")
            time.sleep(0.1)
            
        if not initialize_response:
            print("❌ Timeout waiting for initialize response")
            return
        
        print(f"✅ Initialize response received: {initialize_response.get('result', {}).get('serverInfo', {}).get('name', 'unknown')}")
        
        # Send initialized notification with correct format
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        print(f"Sending initialized notification: {json.dumps(initialized_notification)}")
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()
        
        # Send query request - intentionally simple query that works with empty memory connector
        query_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "sql": "SELECT 'empty_as_fuck' AS status",
                    "catalog": "memory"
                }
            }
        }
        print(f"Sending query request: {json.dumps(query_request)}")
        process.stdin.write(json.dumps(query_request) + "\n")
        process.stdin.flush()
        
        # Read query response with timeout
        start_time = time.time()
        query_response = None
        
        print("Waiting for query response...")
        while time.time() - start_time < timeout:
            response_line = process.stdout.readline().strip()
            if response_line:
                print(f"Got response: {response_line}")
                try:
                    query_response = json.loads(response_line)
                    break
                except json.JSONDecodeError as e:
                    print(f"Error parsing response: {e}")
            time.sleep(0.1)
            
        if not query_response:
            print("❌ Timeout waiting for query response")
            return
        
        print("\n🔍 QUERY RESULTS:")
        
        if "error" in query_response:
            print(f"❌ Error: {query_response['error']}")
        else:
            result = query_response.get('result', {})
            print(f"Query ID: {result.get('query_id', 'unknown')}")
            print(f"Columns: {result.get('columns', [])}")
            print(f"Row count: {result.get('row_count', 0)}")
            print(f"Preview rows: {json.dumps(result.get('preview_rows', []), indent=2)}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        # Properly terminate
        print("\n👋 Test completed. Terminating server process...")
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        
    return query_response

if __name__ == "__main__":
    run_quick_query() 