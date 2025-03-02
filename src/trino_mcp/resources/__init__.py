"""
MCP resources for interacting with Trino.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from mcp.server.fastmcp import Context, FastMCP

from trino_mcp.trino_client import TrinoClient


def register_trino_resources(mcp: FastMCP, client: TrinoClient) -> None:
    """
    Register Trino resources with the MCP server.
    
    Args:
        mcp: The MCP server instance.
        client: The Trino client instance.
    """
    
    @mcp.resource("trino://catalog")
    def list_catalogs() -> List[Dict[str, Any]]:
        """
        List all available Trino catalogs.
        """
        return client.get_catalogs()
    
    @mcp.resource("trino://catalog/{catalog}")
    def get_catalog(catalog: str) -> Dict[str, Any]:
        """
        Get information about a specific Trino catalog.
        """
        # For now, just return basic info - could be enhanced later
        return {"name": catalog}
    
    @mcp.resource("trino://catalog/{catalog}/schemas")
    def list_schemas(catalog: str) -> List[Dict[str, Any]]:
        """
        List all schemas in a Trino catalog.
        """
        return client.get_schemas(catalog)
    
    @mcp.resource("trino://catalog/{catalog}/schema/{schema}")
    def get_schema(catalog: str, schema: str) -> Dict[str, Any]:
        """
        Get information about a specific Trino schema.
        """
        return {"name": schema, "catalog": catalog}
    
    @mcp.resource("trino://catalog/{catalog}/schema/{schema}/tables")
    def list_tables(catalog: str, schema: str) -> List[Dict[str, Any]]:
        """
        List all tables in a Trino schema.
        """
        return client.get_tables(catalog, schema)
    
    @mcp.resource("trino://catalog/{catalog}/schema/{schema}/table/{table}")
    def get_table(catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """
        Get information about a specific Trino table.
        """
        return client.get_table_details(catalog, schema, table)
    
    @mcp.resource("trino://catalog/{catalog}/schema/{schema}/table/{table}/columns")
    def list_columns(catalog: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """
        List all columns in a Trino table.
        """
        return client.get_columns(catalog, schema, table)
    
    @mcp.resource("trino://catalog/{catalog}/schema/{schema}/table/{table}/column/{column}")
    def get_column(catalog: str, schema: str, table: str, column: str) -> Dict[str, Any]:
        """
        Get information about a specific Trino column.
        """
        columns = client.get_columns(catalog, schema, table)
        for col in columns:
            if col["name"] == column:
                return col
        
        # If column not found, return a basic structure
        return {
            "name": column,
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "error": "Column not found"
        }
    
    @mcp.resource("trino://query/{query_id}")
    def get_query_result(query_id: str) -> Dict[str, Any]:
        """
        Get the result of a specific Trino query by its ID.
        """
        # This is a placeholder, as we don't store query results by ID in this basic implementation
        # In a real implementation, you would look up the query results from a cache or storage
        return {
            "query_id": query_id,
            "error": "Query results not available. This resource is for demonstration purposes only."
        }
