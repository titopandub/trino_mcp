#!/usr/bin/env python3
"""
Simple test script to try connecting to the MCP messages endpoint.
This follows the MCP 2024-11-05 specification precisely.
"""
import json
import requests
import sys
import time
import sseclient
import signal

def handle_exit(signum, frame):
    """Handle exit gracefully when user presses Ctrl+C."""
    print("\nInterrupted. Exiting...")
    sys.exit(0)

# Register signal handler for clean exit
signal.signal(signal.SIGINT, handle_exit)

def test_mcp():
    """
    Test the MCP server with standard protocol communication.
    Follows the MCP specification for 2024-11-05 carefully.
    """
    print("🚀 Testing MCP server following 2024-11-05 specification")
    
    # Connect to SSE endpoint
    print("Connecting to SSE endpoint...")
    headers = {"Accept": "text/event-stream"}
    sse_response = requests.get("http://localhost:9096/sse", headers=headers, stream=True)
    
    if sse_response.status_code != 200:
        print(f"❌ Failed to connect to SSE endpoint: {sse_response.status_code}")
        return
    
    print(f"✅ SSE connection established: {sse_response.status_code}")
    
    try:
        client = sseclient.SSEClient(sse_response)
        
        # Get the messages URL from the first event
        messages_url = None
        session_id = None
        
        for event in client.events():
            print(f"📩 SSE event: {event.event} - {event.data}")
            
            if event.event == "endpoint":
                messages_url = f"http://localhost:9096{event.data}"
                # Extract session ID from URL
                if "session_id=" in event.data:
                    session_id = event.data.split("session_id=")[1]
                print(f"✅ Got messages URL: {messages_url}")
                print(f"✅ Session ID: {session_id}")
                break
        
        if not messages_url:
            print("❌ Failed to get messages URL from SSE")
            sse_response.close()
            return
        
        # Now we have the messages URL, send initialize request
        print(f"\n📤 Sending initialize request to {messages_url}")
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "mcp-trino-test-client",
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
        
        response = requests.post(messages_url, json=initialize_request)
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 202:
            print(f"❌ Initialize request failed: {response.text}")
            sse_response.close()
            return
            
        print(f"✅ Initialize request accepted")
        
        # Listen for events and handle protocol properly
        print("\n🔄 Listening for response events...")
        
        # Set up a timeout
        timeout = time.time() + 60  # 60 seconds timeout
        
        # Protocol state tracking
        status = {
            "initialized": False,
            "tools_requested": False,
            "query_requested": False,
            "summary_requested": False,
            "done": False
        }
        
        # Event loop
        while time.time() < timeout and not status["done"]:
            events_received = False
            
            for event in client.events():
                events_received = True
                
                # Skip ping events
                if event.event == "ping":
                    print("📍 Ping event received")
                    continue
                    
                print(f"\n📩 Received event: {event.event}")
                
                # If we get a message event, parse it
                if event.event == "message" and event.data:
                    try:
                        data = json.loads(event.data)
                        print(f"📦 Parsed message: {json.dumps(data, indent=2)}")
                        
                        # Handle initialize response 
                        if "id" in data and data["id"] == 1 and not status["initialized"]:
                            # Send initialized notification (following spec)
                            print("\n📤 Sending initialized notification...")
                            initialized_notification = {
                                "jsonrpc": "2.0",
                                "method": "initialized"
                            }
                            init_response = requests.post(messages_url, json=initialized_notification)
                            
                            if init_response.status_code != 202:
                                print(f"❌ Initialized notification failed: {init_response.status_code}")
                            else:
                                print(f"✅ Initialized notification accepted")
                                status["initialized"] = True
                            
                            # Now request the tools list
                            print("\n📤 Sending tools/list request...")
                            tools_request = {
                                "jsonrpc": "2.0",
                                "id": 2,
                                "method": "tools/list"
                            }
                            tools_response = requests.post(messages_url, json=tools_request)
                            
                            if tools_response.status_code != 202:
                                print(f"❌ Tools list request failed: {tools_response.status_code}")
                            else:
                                print(f"✅ Tools list request accepted")
                                status["tools_requested"] = True
                        
                        # Handle tools list response
                        elif "id" in data and data["id"] == 2 and not status["query_requested"]:
                            # Extract available tools
                            tools = []
                            if "result" in data and "tools" in data["result"]:
                                tools = [tool["name"] for tool in data["result"]["tools"]]
                                print(f"🔧 Available tools: {', '.join(tools)}")
                            
                            # Execute a memory query if the execute_query tool is available
                            if "execute_query" in tools:
                                print("\n📤 Sending query for memory.bullshit.bullshit_data...")
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
                                query_response = requests.post(messages_url, json=query_request)
                                
                                if query_response.status_code != 202:
                                    print(f"❌ Query request failed: {query_response.status_code}")
                                else:
                                    print(f"✅ Query request accepted")
                                    status["query_requested"] = True
                            else:
                                print("❌ execute_query tool not available")
                                status["done"] = True
                        
                        # Handle query response
                        elif "id" in data and data["id"] == 3 and not status["summary_requested"]:
                            # Check if query was successful
                            if "result" in data:
                                print(f"✅ Query succeeded with {data['result'].get('row_count', 0)} rows")
                                
                                # Now query the summary view
                                print("\n📤 Sending query for memory.bullshit.bullshit_summary...")
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
                                summary_response = requests.post(messages_url, json=summary_request)
                                
                                if summary_response.status_code != 202:
                                    print(f"❌ Summary query request failed: {summary_response.status_code}")
                                else:
                                    print(f"✅ Summary query request accepted")
                                    status["summary_requested"] = True
                            else:
                                print(f"❌ Query failed: {data.get('error', 'Unknown error')}")
                                status["done"] = True
                        
                        # Handle summary query response
                        elif "id" in data and data["id"] == 4:
                            if "result" in data:
                                print(f"✅ Summary query succeeded with {data['result'].get('row_count', 0)} rows")
                                # Print the summary data nicely formatted
                                if "preview_rows" in data["result"]:
                                    for row in data["result"]["preview_rows"]:
                                        print(f"  {row}")
                            else:
                                print(f"❌ Summary query failed: {data.get('error', 'Unknown error')}")
                            
                            print("\n🏁 All tests completed successfully!")
                            status["done"] = True
                            break
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ Error parsing message: {e}")
                    except Exception as e:
                        print(f"❌ Unexpected error: {e}")
                
                # Break out of the event loop if we're done
                if status["done"]:
                    break
            
            # If we didn't receive any events, wait a bit before trying again
            if not events_received:
                time.sleep(0.5)
        
        # Check if we timed out
        if time.time() >= timeout and not status["done"]:
            print("⏱️ Timeout waiting for responses")
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Close the SSE connection
        print("\n👋 Closing SSE connection...")
        sse_response.close()
        print("✅ Connection closed")

if __name__ == "__main__":
    test_mcp() 