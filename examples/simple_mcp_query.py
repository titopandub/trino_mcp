#!/usr/bin/env python3
"""
Simple example script for Trino MCP querying using STDIO transport.

This demonstrates the most basic end-to-end flow of running a query through MCP.
"""
import json
import subprocess
import sys
import time

def run_query_with_mcp(sql_query: str, catalog: str = "memory"):
    """
    Run a SQL query against Trino using the MCP STDIO transport.
    
    Args:
        sql_query: The SQL query to run
        catalog: The catalog to use (default: memory)
        
    Returns:
        The query results (if successful)
    """
    print(f"🚀 Running query with Trino MCP")
    print(f"SQL: {sql_query}")
    print(f"Catalog: {catalog}")
    
    # Start the MCP server with STDIO transport
    cmd = [
        "docker", "exec", "-i", "trino_mcp_trino-mcp_1", 
        "python", "-m", "trino_mcp.server", 
        "--transport", "stdio", 
        "--trino-host", "trino",
        "--trino-port", "8080",
        "--trino-user", "trino", 
        "--trino-catalog", catalog
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Allow server to start
        time.sleep(1)
        
        # Function to send requests and get responses
        def send_request(request):
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json)
            process.stdin.flush()
            
            response = process.stdout.readline()
            if response:
                return json.loads(response)
            return None
        
        # Step 1: Initialize MCP
        print("\n1. Initializing MCP...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "simple-example",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": True
                }
            }
        }
        
        init_response = send_request(init_request)
        if not init_response:
            raise Exception("Failed to initialize MCP")
        
        print("✅ MCP initialized")
        
        # Step 2: Send initialized notification
        init_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        send_request(init_notification)
        
        # Step 3: Execute query
        print("\n2. Executing query...")
        query_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "sql": sql_query,
                    "catalog": catalog
                }
            }
        }
        
        query_response = send_request(query_request)
        if not query_response:
            raise Exception("Failed to execute query")
        
        if "error" in query_response:
            error = query_response["error"]
            print(f"❌ Query failed: {error}")
            return None
        
        # Print and return results
        result = query_response["result"]
        print("\n✅ Query executed successfully!")
        
        # Format results for display
        if "columns" in result:
            print("\nColumns:", ", ".join(result.get("columns", [])))
            print(f"Row count: {result.get('row_count', 0)}")
            
            if "preview_rows" in result:
                print("\nResults:")
                for i, row in enumerate(result["preview_rows"]):
                    print(f"  {i+1}. {row}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Clean up
        if 'process' in locals():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

if __name__ == "__main__":
    # Get query from command line args or use default
    query = "SELECT 'Hello from Trino MCP!' AS greeting"
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    # Run the query    
    run_query_with_mcp(query) 