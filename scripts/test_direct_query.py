#!/usr/bin/env python3
"""
Direct test script that bypasses MCP and uses the Trino client directly.
This helps determine if the issue is with the MCP protocol or with Trino.
"""
import time
import argparse
from typing import Optional, Dict, Any

# Import the client class from the module
from src.trino_mcp.trino_client import TrinoClient
from src.trino_mcp.config import TrinoConfig

def main():
    """
    Run direct queries against Trino without using MCP.
    """
    print("Direct Trino test - bypassing MCP")
    
    # Configure Trino client
    config = TrinoConfig(
        host="localhost",
        port=9095,  # The exposed Trino port
        user="trino",
        catalog="memory",
        schema=None,
        http_scheme="http"
    )
    
    client = TrinoClient(config)
    
    try:
        # Connect to Trino
        print("Connecting to Trino...")
        client.connect()
        print("Connected successfully!")
        
        # List catalogs
        print("\nListing catalogs:")
        catalogs = client.get_catalogs()
        for catalog in catalogs:
            print(f"- {catalog['name']}")
            
        # List schemas in memory catalog
        print("\nListing schemas in memory catalog:")
        schemas = client.get_schemas("memory")
        for schema in schemas:
            print(f"- {schema['name']}")
            
        # Look for our test schema
        if any(schema['name'] == 'bullshit' for schema in schemas):
            print("\nFound our test schema 'bullshit'")
            
            # List tables
            print("\nListing tables in memory.bullshit:")
            tables = client.get_tables("memory", "bullshit")
            for table in tables:
                print(f"- {table['name']}")
                
            # Query the data table
            if any(table['name'] == 'bullshit_data' for table in tables):
                print("\nQuerying memory.bullshit.bullshit_data:")
                result = client.execute_query("SELECT * FROM memory.bullshit.bullshit_data")
                
                # Print columns
                print(f"Columns: {', '.join(result.columns)}")
                
                # Print rows
                print(f"Rows ({result.row_count}):")
                for row in result.rows:
                    print(f"  {row}")
                    
                # Query the summary view
                if any(table['name'] == 'bullshit_summary' for table in tables):
                    print("\nQuerying memory.bullshit.bullshit_summary:")
                    result = client.execute_query(
                        "SELECT * FROM memory.bullshit.bullshit_summary ORDER BY count DESC"
                    )
                    
                    # Print columns
                    print(f"Columns: {', '.join(result.columns)}")
                    
                    # Print rows
                    print(f"Rows ({result.row_count}):")
                    for row in result.rows:
                        print(f"  {row}")
                else:
                    print("Summary view not found")
            else:
                print("Data table not found")
        else:
            print("Test schema 'bullshit' not found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect
        if client.conn:
            print("\nDisconnecting from Trino...")
            client.disconnect()
            print("Disconnected.")

if __name__ == "__main__":
    main() 