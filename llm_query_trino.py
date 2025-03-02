#!/usr/bin/env python3
"""
Simple wrapper script for LLMs to query Trino through MCP.
This script handles all the MCP protocol complexity, so the LLM only needs to focus on SQL.

Usage:
  python llm_query_trino.py "SELECT * FROM memory.bullshit.real_bullshit_data LIMIT 5"
"""
import json
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional

# Default configurations - modify as needed
DEFAULT_CATALOG = "memory"
DEFAULT_SCHEMA = "bullshit"

def query_trino(sql_query: str, catalog: str = DEFAULT_CATALOG, schema: Optional[str] = DEFAULT_SCHEMA) -> Dict[str, Any]:
    """
    Run a SQL query against Trino through MCP and return the results.
    
    Args:
        sql_query: The SQL query to execute
        catalog: Catalog name (default: memory)
        schema: Schema name (default: bullshit)
        
    Returns:
        Dictionary with query results or error
    """
    print(f"\n🔍 Running query via Trino MCP:\n{sql_query}")
    
    # Start the MCP server with STDIO transport
    cmd = [
        "docker", "exec", "-i", "trino_mcp_trino-mcp_1", 
        "python", "-m", "trino_mcp.server", 
        "--transport", "stdio", 
        "--debug",
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
        
        # Wait for MCP server to start
        time.sleep(2)
        
        # Helper function to send requests
        def send_request(request, expect_response=True):
            request_str = json.dumps(request) + "\n"
            process.stdin.write(request_str)
            process.stdin.flush()
            
            if not expect_response:
                return None
                
            response_str = process.stdout.readline()
            if response_str:
                return json.loads(response_str)
            return None
        
        # Step 1: Initialize MCP
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "llm-query-client",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": True
                }
            }
        }
        
        init_response = send_request(init_request)
        if not init_response:
            return {"error": "Failed to initialize MCP"}
        
        # Step 2: Send initialized notification
        init_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        send_request(init_notification, expect_response=False)
        
        # Step 3: Execute query
        query_args = {"sql": sql_query, "catalog": catalog}
        if schema:
            query_args["schema"] = schema
            
        query_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": query_args
            }
        }
        
        query_response = send_request(query_request)
        if not query_response:
            return {"error": "No response received for query"}
            
        if "error" in query_response:
            return {"error": query_response["error"]}
        
        # Step 4: Parse the content
        try:
            # Extract nested result content
            content_text = query_response.get("result", {}).get("content", [{}])[0].get("text", "{}")
            result_data = json.loads(content_text)
            
            # Clean up the results for easier consumption
            return {
                "success": True,
                "query_id": result_data.get("query_id", "unknown"),
                "columns": result_data.get("columns", []),
                "row_count": result_data.get("row_count", 0),
                "rows": result_data.get("preview_rows", []),
                "execution_time_ms": result_data.get("query_time_ms", 0)
            }
        except Exception as e:
            return {
                "error": f"Error parsing results: {str(e)}",
                "raw_response": query_response
            }
            
    except Exception as e:
        return {"error": f"Error: {str(e)}"}
    finally:
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

def format_results(results: Dict[str, Any]) -> str:
    """Format query results for display"""
    if "error" in results:
        return f"❌ Error: {results['error']}"
    
    if not results.get("success"):
        return f"❌ Query failed: {results}"
    
    output = [
        f"✅ Query executed successfully!",
        f"📊 Rows: {results['row_count']}",
        f"⏱️ Execution Time: {results['execution_time_ms']:.2f}ms",
        f"\nColumns: {', '.join(results['columns'])}",
        f"\nResults:"
    ]
    
    # Table header
    if results["columns"]:
        header = " | ".join(f"{col.upper()}" for col in results["columns"])
        output.append(header)
        output.append("-" * len(header))
    
    # Table rows
    for row in results["rows"]:
        values = []
        for col in results["columns"]:
            values.append(str(row.get(col, "NULL")))
        output.append(" | ".join(values))
    
    return "\n".join(output)

def main():
    """Run a query from command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python llm_query_trino.py 'SELECT * FROM memory.bullshit.real_bullshit_data LIMIT 5'")
        sys.exit(1)
    
    # Get the SQL query from command line
    sql_query = sys.argv[1]
    
    # Parse optional catalog and schema
    catalog = DEFAULT_CATALOG
    schema = DEFAULT_SCHEMA
    
    if len(sys.argv) > 2:
        catalog = sys.argv[2]
    
    if len(sys.argv) > 3:
        schema = sys.argv[3]
    
    # Execute the query
    results = query_trino(sql_query, catalog, schema)
    
    # Print formatted results
    print(format_results(results))

if __name__ == "__main__":
    main() 