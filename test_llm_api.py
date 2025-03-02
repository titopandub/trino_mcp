#!/usr/bin/env python3
"""
Test script for the LLM API endpoint in the Trino MCP server.

This script tests the various endpoints of the API server to verify functionality.
"""

import json
import requests
from rich.console import Console
from rich.table import Table
from typing import Dict, Any, List, Optional

# Configuration
API_HOST = "localhost"
API_PORT = 9097
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

console = Console()

def test_endpoint(url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Test an endpoint and return the response with detailed info."""
    console.print(f"\n[bold blue]Testing {method} {url}[/bold blue]")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            console.print(f"[bold red]Unsupported method: {method}[/bold red]")
            return {"success": False, "status_code": 0, "error": f"Unsupported method: {method}"}
        
        status_color = "green" if response.status_code < 400 else "red"
        console.print(f"Status: [bold {status_color}]{response.status_code} - {response.reason}[/bold {status_color}]")
        
        # Try to parse response as JSON
        try:
            data = response.json()
            console.print("Response data:")
            console.print(json.dumps(data, indent=2))
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": data
            }
        except ValueError:
            console.print(f"Response text: {response.text[:500]}")
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "text": response.text[:500]
            }
            
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        return {"success": False, "error": str(e)}

def discover_all_endpoints() -> None:
    """Discover available endpoints by trying common paths."""
    console.print("[bold yellow]Discovering endpoints...[/bold yellow]")
    
    # Common endpoints to check
    endpoints = [
        "/",
        "/api",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/query",
        "/query"
    ]
    
    results = []
    for endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        result = test_endpoint(url)
        results.append({
            "endpoint": endpoint,
            "status": result["status_code"] if "status_code" in result else "Error",
            "success": result.get("success", False)
        })
    
    # Display results in a table
    table = Table(title="API Endpoint Discovery Results")
    table.add_column("Endpoint", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Result", style="green")
    
    for result in results:
        status = str(result["status"])
        status_style = "green" if result["success"] else "red"
        result_text = "✅ Available" if result["success"] else "❌ Not Available"
        table.add_row(result["endpoint"], f"[{status_style}]{status}[/{status_style}]", result_text)
    
    console.print(table)

def test_api_docs() -> bool:
    """Test the API documentation endpoint."""
    console.print("\n[bold yellow]Testing API documentation...[/bold yellow]")
    
    # Try the /docs endpoint first
    url = f"{API_BASE_URL}/docs"
    result = test_endpoint(url)
    
    if result.get("success", False):
        console.print("[bold green]API documentation is available at /docs[/bold green]")
        return True
    else:
        console.print("[bold red]API documentation not available at /docs[/bold red]")
        
        # Try the OpenAPI JSON endpoint
        url = f"{API_BASE_URL}/openapi.json"
        result = test_endpoint(url)
        
        if result.get("success", False):
            console.print("[bold green]OpenAPI spec is available at /openapi.json[/bold green]")
            
            # Try to extract query endpoint from the spec
            if "data" in result:
                try:
                    paths = result["data"].get("paths", {})
                    for path, methods in paths.items():
                        if "post" in methods and ("/query" in path or "/api/query" in path):
                            console.print(f"[bold green]Found query endpoint in OpenAPI spec: {path}[/bold green]")
                            return True
                except:
                    console.print("[bold red]Failed to parse OpenAPI spec[/bold red]")
            
            return True
        else:
            console.print("[bold red]OpenAPI spec not available[/bold red]")
            return False

def test_valid_query() -> bool:
    """Test a valid SQL query against the API."""
    console.print("\n[bold yellow]Testing valid SQL query...[/bold yellow]")
    
    # Try multiple potential query endpoints
    query_payload = {
        "query": "SELECT 1 AS test",
        "catalog": "memory",
        "schema": "default"
    }
    
    endpoints = ["/api/query", "/query"]
    
    for endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        console.print(f"[bold]Trying endpoint: {endpoint}[/bold]")
        
        result = test_endpoint(url, method="POST", data=query_payload)
        
        if result.get("success", False):
            console.print(f"[bold green]Successfully executed query at {endpoint}[/bold green]")
            
            # Display results if available
            if "data" in result and "results" in result["data"]:
                display_query_results(result["data"]["results"])
            
            return True
    
    console.print("[bold red]Failed to execute query on any endpoint[/bold red]")
    return False

def test_invalid_query() -> bool:
    """Test an invalid SQL query to check error handling."""
    console.print("\n[bold yellow]Testing invalid SQL query (error handling)...[/bold yellow]")
    
    query_payload = {
        "query": "SELECT * FROM nonexistent_table",
        "catalog": "memory",
        "schema": "default"
    }
    
    # Try the same endpoints as for valid query
    endpoints = ["/api/query", "/query"]
    
    for endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        console.print(f"[bold]Trying endpoint: {endpoint}[/bold]")
        
        result = test_endpoint(url, method="POST", data=query_payload)
        
        # Check if we got a proper error response (should be 400 Bad Request)
        if "status_code" in result and result["status_code"] == 400:
            console.print(f"[bold green]API correctly rejected invalid query at {endpoint} with 400 status[/bold green]")
            return True
    
    console.print("[bold red]Failed to properly handle invalid query on any endpoint[/bold red]")
    return False

def display_query_results(results: Dict[str, Any]) -> None:
    """Display query results in a formatted table."""
    if not results or "rows" not in results or not results["rows"]:
        console.print("[italic yellow]No results returned[/italic yellow]")
        return
    
    table = Table(title="Query Results")
    
    # Add columns to the table
    for column in results.get("columns", []):
        table.add_column(column)
    
    # Add data rows
    for row in results.get("rows", []):
        if isinstance(row, dict):
            table.add_row(*[str(row.get(col, "")) for col in results.get("columns", [])])
        elif isinstance(row, list):
            table.add_row(*[str(val) for val in row])
    
    console.print(table)
    console.print(f"[italic]Total rows: {results.get('row_count', len(results.get('rows', [])))}[/italic]")
    if "execution_time_ms" in results:
        console.print(f"[italic]Execution time: {results['execution_time_ms']} ms[/italic]")

def main() -> None:
    """Run all tests."""
    console.print("[bold green]=== Trino MCP LLM API Test ===\n[/bold green]")
    
    # First discover all available endpoints
    discover_all_endpoints()
    
    # Test API documentation
    docs_available = test_api_docs()
    
    # Only test queries if docs are available
    if docs_available:
        test_valid_query()
        test_invalid_query()
    else:
        console.print("[bold red]Skipping query tests as API documentation is not available[/bold red]")
    
    console.print("\n[bold green]=== Test completed ===\n[/bold green]")

if __name__ == "__main__":
    main() 