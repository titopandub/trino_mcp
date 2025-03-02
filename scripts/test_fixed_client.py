#!/usr/bin/env python3
"""
Fixed test script for the MCP server that uses the correct notification format.
This should actually work with MCP 1.3.0.
"""
import json
import requests
import sys
import time
import sseclient
from rich.console import Console

console = Console()

def test_mcp():
    """
    Test the MCP server with proper message formats.
    Fixes the notification format to work with MCP 1.3.0.
    """
    console.print("[bold green]🚀 Starting MCP client test with fixed notification format[/]")
    
    # Connect to SSE endpoint
    console.print("[bold blue]Connecting to SSE endpoint...[/]")
    headers = {"Accept": "text/event-stream"}
    sse_response = requests.get("http://localhost:9096/sse", headers=headers, stream=True)
    client = sseclient.SSEClient(sse_response)
    
    # Get the messages URL from the first event
    messages_url = None
    session_id = None
    
    for event in client.events():
        console.print(f"[cyan]SSE event:[/] {event.event}")
        console.print(f"[cyan]SSE data:[/] {event.data}")
        
        if event.event == "endpoint":
            messages_url = f"http://localhost:9096{event.data}"
            # Extract session ID from URL
            if "session_id=" in event.data:
                session_id = event.data.split("session_id=")[1]
            console.print(f"[green]Got messages URL:[/] {messages_url}")
            console.print(f"[green]Session ID:[/] {session_id}")
            break
    
    if not messages_url:
        console.print("[bold red]Failed to get messages URL from SSE[/]")
        return
    
    # Now we have the messages URL, send initialize request
    console.print(f"\n[bold blue]Sending initialize request to {messages_url}[/]")
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "fixed-test-client",
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
    
    try:
        response = requests.post(messages_url, json=initialize_request)
        console.print(f"[cyan]Status code:[/] {response.status_code}")
        console.print(f"[cyan]Response:[/] {response.text}")
        
        # Continue listening for events to get the response
        console.print("\n[bold blue]Listening for response events...[/]")
        
        # Start a timeout counter
        start_time = time.time()
        timeout = 30  # 30 seconds timeout
        
        # Keep listening for events
        for event in client.events():
            # Skip ping events
            if event.event == "ping":
                continue
                
            console.print(f"[magenta]Event type:[/] {event.event}")
            console.print(f"[magenta]Event data:[/] {event.data}")
            
            # If we get a message event, parse it
            if event.event == "message" and event.data:
                try:
                    data = json.loads(event.data)
                    console.print(f"[green]Parsed message:[/] {json.dumps(data, indent=2)}")
                    
                    # Check if this is a response to our initialize request
                    if "id" in data and data["id"] == 1:
                        # Send an initialization notification with CORRECT FORMAT
                        console.print("\n[bold blue]Sending initialized notification with correct format...[/]")
                        initialized_notification = {
                            "jsonrpc": "2.0",
                            "method": "notifications/initialized",  # FIXED: correct method name
                            "params": {}  # FIXED: added required params
                        }
                        response = requests.post(messages_url, json=initialized_notification)
                        console.print(f"[cyan]Status code:[/] {response.status_code}")
                        console.print(f"[cyan]Response:[/] {response.text}")
                        
                        # Now send a tools/list request
                        console.print("\n[bold blue]Sending tools/list request...[/]")
                        tools_request = {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/list"
                        }
                        response = requests.post(messages_url, json=tools_request)
                        console.print(f"[cyan]Status code:[/] {response.status_code}")
                        console.print(f"[cyan]Response:[/] {response.text}")
                        
                    # Check if this is a response to our tools/list request
                    if "id" in data and data["id"] == 2:
                        # Now send a resources/list request for trino catalogs
                        console.print("\n[bold blue]Sending resources/list request for trino catalogs...[/]")
                        resources_request = {
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "resources/list",
                            "params": {
                                "source": "trino://catalog"
                            }
                        }
                        response = requests.post(messages_url, json=resources_request)
                        console.print(f"[cyan]Status code:[/] {response.status_code}")
                        console.print(f"[cyan]Response:[/] {response.text}")
                        
                    # If we get the resource list, try to execute a query
                    if "id" in data and data["id"] == 3:
                        console.print("\n[bold green]🔥 Got resources! Now trying to execute a query...[/]")
                        query_request = {
                            "jsonrpc": "2.0",
                            "id": 4,
                            "method": "tools/call",
                            "params": {
                                "name": "execute_query",
                                "arguments": {
                                    "sql": "SELECT 1 AS test_value, 'it works!' AS message",
                                    "catalog": "memory"
                                }
                            }
                        }
                        response = requests.post(messages_url, json=query_request)
                        console.print(f"[cyan]Status code:[/] {response.status_code}")
                        console.print(f"[cyan]Response:[/] {response.text}")
                        
                except Exception as e:
                    console.print(f"[bold red]Error parsing message:[/] {e}")
                    
            # Check timeout
            if time.time() - start_time > timeout:
                console.print("[bold yellow]Timeout waiting for response[/]")
                break
                
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting...[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
    finally:
        # Close the SSE connection
        sse_response.close()
        console.print("[bold green]Test completed. Connection closed.[/]")
        
if __name__ == "__main__":
    test_mcp() 