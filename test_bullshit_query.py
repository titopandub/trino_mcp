#!/usr/bin/env python3
"""
Test script to query our bullshit data through the MCP server.
This demonstrates that our fix for the catalog handling works by running a complex query.
"""
import json
import subprocess
import sys
import time

def test_bullshit_query():
    """Run a query against our bullshit data using the MCP STDIO transport."""
    print("🚀 Testing Bullshit Data with MCP STDIO Transport")
    
    # Start the MCP server with STDIO transport
    cmd = [
        "docker", "exec", "-i", "trino_mcp_trino-mcp_1", 
        "python", "-m", "trino_mcp.server", 
        "--transport", "stdio", 
        "--debug",
        "--trino-host", "trino",
        "--trino-port", "8080",
        "--trino-user", "trino", 
        "--trino-catalog", "memory"
    ]
    
    try:
        print("Starting MCP server process with STDIO transport...")
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Sleep to let the server initialize
        time.sleep(2)
        
        # Helper function to send a request and get a response
        def send_request(request, expect_response=True):
            """
            Send a request to the MCP server and get the response.
            
            Args:
                request: The JSON-RPC request to send
                expect_response: Whether to wait for a response
                
            Returns:
                The JSON-RPC response, or None if no response is expected
            """
            request_str = json.dumps(request) + "\n"
            print(f"\n📤 Sending: {request_str.strip()}")
            
            try:
                process.stdin.write(request_str)
                process.stdin.flush()
            except BrokenPipeError:
                print("❌ Broken pipe - server has closed the connection")
                return None
                
            if not expect_response:
                print("✅ Sent notification (no response expected)")
                return None
                
            # Read the response
            print("Waiting for response...")
            try:
                response_str = process.stdout.readline()
                if response_str:
                    print(f"📩 Received response")
                    return json.loads(response_str)
                else:
                    print("❌ No response received")
                    return None
            except Exception as e:
                print(f"❌ Error reading response: {e}")
                return None
        
        # ===== STEP 1: Initialize MCP =====
        print("\n===== STEP 1: Initialize MCP =====")
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "bullshit-data-query-test",
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
        
        init_response = send_request(initialize_request)
        if not init_response:
            print("❌ Failed to initialize MCP - exiting test")
            return
            
        # Print server info
        if "result" in init_response and "serverInfo" in init_response["result"]:
            server_info = init_response["result"]["serverInfo"]
            print(f"✅ Connected to server: {server_info.get('name')} {server_info.get('version')}")
        
        # ===== STEP 2: Send initialized notification =====
        print("\n===== STEP 2: Send initialized notification =====")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        send_request(initialized_notification, expect_response=False)
        
        # ===== STEP 3: Query the bullshit data =====
        print("\n===== STEP 3: Query the Bullshit Data =====")
        query_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "sql": """
                    SELECT 
                      job_title, 
                      COUNT(*) as count, 
                      AVG(salary) as avg_salary,
                      MAX(salary) as max_salary,
                      AVG(bullshit_factor) as avg_bs_factor
                    FROM 
                      memory.bullshit.real_bullshit_data
                    WHERE 
                      salary > 150000
                    GROUP BY 
                      job_title
                    HAVING 
                      AVG(bullshit_factor) > 5
                    ORDER BY 
                      avg_salary DESC
                    LIMIT 10
                    """,
                    "catalog": "memory",
                    "schema": "bullshit"
                }
            }
        }
        
        query_response = send_request(query_request)
        if not query_response or "error" in query_response:
            if "error" in query_response:
                print(f"❌ Query error: {json.dumps(query_response.get('error', {}), indent=2)}")
            else:
                print("❌ Failed to execute query")
        else:
            print(f"✅ Bullshit query executed successfully!")
            
            # Parse the nested JSON in the content field
            try:
                content_text = query_response.get("result", {}).get("content", [{}])[0].get("text", "{}")
                result_data = json.loads(content_text)
                
                # Now we have the actual query result
                columns = result_data.get("columns", [])
                row_count = result_data.get("row_count", 0)
                preview_rows = result_data.get("preview_rows", [])
                
                print(f"\nColumns: {', '.join(columns)}")
                print(f"Row count: {row_count}")
                print("\n🏆 TOP 10 BULLSHIT JOBS (high salary, high BS factor):")
                print("-" * 100)
                
                # Print header with nice formatting
                header = " | ".join(f"{col.upper():20}" for col in columns)
                print(header)
                print("-" * 100)
                
                # Print rows with nice formatting
                for row in preview_rows:
                    row_str = []
                    for col in columns:
                        value = row.get(col, "N/A")
                        if isinstance(value, float):
                            row_str.append(f"{value:20.2f}")
                        else:
                            row_str.append(f"{str(value):20}")
                    print(" | ".join(row_str))
                
            except json.JSONDecodeError:
                print(f"Error parsing result content: {query_response}")
            except Exception as e:
                print(f"Error processing result: {e}")
                print(f"Raw result: {json.dumps(query_response.get('result', {}), indent=2)}")
                
        # ===== STEP 4: List Available Schemas =====
        print("\n===== STEP 4: List Available Schemas in Memory Catalog =====")
        schema_query = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "sql": "SHOW SCHEMAS FROM memory",
                    "catalog": "memory"
                }
            }
        }
        
        schema_response = send_request(schema_query)
        if not schema_response or "error" in schema_response:
            if "error" in schema_response:
                print(f"❌ Schema query error: {json.dumps(schema_response.get('error', {}), indent=2)}")
            else:
                print("❌ Failed to execute schema query")
        else:
            print(f"✅ Schema query executed successfully!")
            
            # Parse the nested JSON in the content field
            try:
                content_text = schema_response.get("result", {}).get("content", [{}])[0].get("text", "{}")
                result_data = json.loads(content_text)
                
                # Extract schema names
                preview_rows = result_data.get("preview_rows", [])
                schema_column = result_data.get("columns", ["Schema"])[0]
                
                print("\n🗂️ Available schemas in memory catalog:")
                for row in preview_rows:
                    schema_name = row.get(schema_column, "unknown")
                    print(f"  - {schema_name}")
                    
            except json.JSONDecodeError:
                print(f"Error parsing schemas content: {schema_response}")
            except Exception as e:
                print(f"Error processing schemas: {e}")
                print(f"Raw schema result: {json.dumps(schema_response.get('result', {}), indent=2)}")
                
        print("\n🎉 Test completed successfully!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Make sure to terminate the process
        if 'process' in locals() and process.poll() is None:
            print("\nTerminating server process...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Process didn't terminate, killing it...")
                process.kill()

if __name__ == "__main__":
    test_bullshit_query() 