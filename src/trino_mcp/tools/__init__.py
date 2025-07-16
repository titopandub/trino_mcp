"""
MCP tools for executing operations on Trino.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from mcp.server.fastmcp import Context, FastMCP

from trino_mcp.trino_client import TrinoClient


def register_trino_tools(mcp: FastMCP, client: TrinoClient) -> None:
    """
    Register Trino tools with the MCP server.
    
    Args:
        mcp: The MCP server instance.
        client: The Trino client instance.
    """
    
    @mcp.tool()
    def execute_query(
        sql: str, 
        catalog: Optional[str] = None, 
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL query against Trino.
        
        Args:
            sql: The SQL query to execute.
            catalog: Optional catalog name to use for the query.
            schema: Optional schema name to use for the query.
            
        Returns:
            Dict[str, Any]: Query results including metadata.
        """
        logger.info(f"Executing query: {sql}")
        
        try:
            result = client.execute_query(sql, catalog, schema)
            
            # Format the result in a structured way
            formatted_result = {
                "query_id": result.query_id,
                "columns": result.columns,
                "row_count": result.row_count,
                "query_time_ms": result.query_time_ms
            }
            
            # Add preview of results (first 20 rows)
            preview_rows = []
            max_preview_rows = min(20, len(result.rows))
            
            for i in range(max_preview_rows):
                row_dict = {}
                for j, col in enumerate(result.columns):
                    row_dict[col] = result.rows[i][j]
                preview_rows.append(row_dict)
                
            formatted_result["preview_rows"] = preview_rows
            
            # Include a resource path for full results
            formatted_result["resource_path"] = f"trino://query/{result.query_id}"
            
            return formatted_result
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Query execution failed: {error_msg}")
            return {
                "error": error_msg,
                "query": sql
            }
    
    @mcp.tool()
    def cancel_query(query_id: str) -> Dict[str, Any]:
        """
        Cancel a running query.
        
        Args:
            query_id: ID of the query to cancel.
            
        Returns:
            Dict[str, Any]: Result of the cancellation operation.
        """
        logger.info(f"Cancelling query: {query_id}")
        
        try:
            success = client.cancel_query(query_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Query {query_id} cancelled successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to cancel query {query_id}"
                }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Query cancellation failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "query_id": query_id
            }
    
    @mcp.tool()
    def inspect_table(
        catalog: str, 
        schema: str, 
        table: str
    ) -> Dict[str, Any]:
        """
        Get detailed metadata about a table.
        
        Args:
            catalog: Catalog name.
            schema: Schema name.
            table: Table name.
            
        Returns:
            Dict[str, Any]: Table metadata including columns, statistics, etc.
        """
        logger.info(f"Inspecting table: {catalog}.{schema}.{table}")
        
        try:
            table_details = client.get_table_details(catalog, schema, table)
            
            # Get additional info from the information_schema if available
            try:
                info_schema_query = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM {catalog}.information_schema.columns
                WHERE table_catalog = '{catalog}'
                AND table_schema = '{schema}'
                AND table_name = '{table}'
                """
                info_schema_result = client.execute_query(info_schema_query)
                
                enhanced_columns = []
                for col in table_details["columns"]:
                    enhanced_col = col.copy()
                    
                    # Find matching info_schema row
                    for row in info_schema_result.rows:
                        if row[0] == col["name"]:
                            enhanced_col["data_type"] = row[1]
                            enhanced_col["is_nullable"] = row[2]
                            enhanced_col["default"] = row[3]
                            break
                            
                    enhanced_columns.append(enhanced_col)
                    
                table_details["columns"] = enhanced_columns
            except Exception as e:
                logger.warning(f"Failed to get column details from information_schema: {e}")
                
            return table_details
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Table inspection failed: {error_msg}")
            return {
                "error": error_msg,
                "catalog": catalog,
                "schema": schema,
                "table": table
            }
