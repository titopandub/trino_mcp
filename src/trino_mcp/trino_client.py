"""
Trino client wrapper for interacting with Trino.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import trino
from loguru import logger

from trino_mcp.config import TrinoConfig


@dataclass
class TrinoQueryResult:
    """A class to represent the result of a Trino query."""
    query_id: str
    columns: List[str]
    rows: List[List[Any]]
    query_time_ms: float
    row_count: int


class TrinoClient:
    """
    A wrapper around the trino-python client to interact with Trino.
    """

    def __init__(self, config: TrinoConfig):
        """
        Initialize the Trino client.
        
        Args:
            config: Trino connection configuration.
        """
        self.config = config
        self.conn = None
        self.current_catalog = config.catalog
        self.current_schema = config.schema
        
    def connect(self) -> None:
        """
        Connect to the Trino server.
        
        This will connect to Trino with the catalog parameter if provided.
        """
        logger.info(f"Connecting to Trino at {self.config.host}:{self.config.port}")
        
        # Create connection params including catalog from config
        conn_params = self.config.connection_params
        
        # Connect to Trino with proper parameters
        self.conn = trino.dbapi.connect(**conn_params)
        
    def disconnect(self) -> None:
        """
        Disconnect from the Trino server.
        """
        if self.conn:
            logger.info("Disconnecting from Trino")
            self.conn.close()
            self.conn = None
            
    def ensure_connection(self) -> None:
        """
        Ensure that the client is connected to Trino.
        """
        if not self.conn:
            self.connect()
            
    def execute_query(
        self, 
        sql: str, 
        catalog: Optional[str] = None, 
        schema: Optional[str] = None
    ) -> TrinoQueryResult:
        """
        Execute a SQL query against Trino.
        
        Important note on catalog handling: This method properly sets the catalog by updating
        the connection parameters, rather than using unreliable "USE catalog" statements. The catalog
        is passed directly to the connection, which is more reliable than SQL-based catalog switching.
        
        Args:
            sql: The SQL query to execute.
            catalog: Optional catalog name to use for the query.
            schema: Optional schema name to use for the query.
            
        Returns:
            TrinoQueryResult: The result of the query.
        """
        # If we're switching catalogs or don't have a connection, we need to reconnect
        use_catalog = catalog or self.current_catalog
        
        if self.conn and (use_catalog != self.current_catalog):
            logger.info(f"Switching catalog from {self.current_catalog} to {use_catalog}, reconnecting...")
            self.disconnect()
        
        # Update current catalog and schema
        self.current_catalog = use_catalog
        if schema:
            self.current_schema = schema
            
        # Update the config catalog before connecting
        if use_catalog:
            self.config.catalog = use_catalog
        
        # Ensure connection with updated catalog
        self.ensure_connection()
        
        # Create a cursor
        cursor = self.conn.cursor()
        
        # If we have a schema, try to set it
        # This still uses a USE statement, but catalogs are now set in the connection
        if self.current_schema:
            try:
                logger.debug(f"Setting schema to {self.current_schema}")
                
                # Make sure to include catalog with schema to avoid errors
                if self.current_catalog:
                    cursor.execute(f"USE {self.current_catalog}.{self.current_schema}")
                else:
                    logger.warning("Cannot set schema without catalog")
            except Exception as e:
                logger.warning(f"Failed to set schema: {e}")
        
        try:
            # Execute the query and time it
            logger.debug(f"Executing query: {sql}")
            start_time = time.time()
            cursor.execute(sql)
            query_time = time.time() - start_time
            
            # Fetch the query ID, metadata and results
            query_id = cursor.stats.get("queryId", "unknown")
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall() if cursor.description else []
            
            return TrinoQueryResult(
                query_id=query_id,
                columns=columns,
                rows=rows,
                query_time_ms=query_time * 1000,
                row_count=len(rows)
            )
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_catalogs(self) -> List[Dict[str, str]]:
        """
        Get a list of all catalogs in Trino.
        
        Returns:
            List[Dict[str, str]]: A list of catalog metadata.
        """
        result = self.execute_query("SHOW CATALOGS")
        return [{"name": row[0]} for row in result.rows]
    
    def get_schemas(self, catalog: str) -> List[Dict[str, str]]:
        """
        Get a list of all schemas in a catalog.
        
        Args:
            catalog: The catalog name.
            
        Returns:
            List[Dict[str, str]]: A list of schema metadata.
        """
        result = self.execute_query(f"SHOW SCHEMAS FROM {catalog}", catalog=catalog)
        return [{"name": row[0], "catalog": catalog} for row in result.rows]
    
    def get_tables(self, catalog: str, schema: str) -> List[Dict[str, str]]:
        """
        Get a list of all tables in a schema.
        
        Args:
            catalog: The catalog name.
            schema: The schema name.
            
        Returns:
            List[Dict[str, str]]: A list of table metadata.
        """
        result = self.execute_query(f"SHOW TABLES FROM {catalog}.{schema}", catalog=catalog, schema=schema)
        return [{"name": row[0], "catalog": catalog, "schema": schema} for row in result.rows]
    
    def get_columns(self, catalog: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """
        Get a list of all columns in a table.
        
        Args:
            catalog: The catalog name.
            schema: The schema name.
            table: The table name.
            
        Returns:
            List[Dict[str, Any]]: A list of column metadata.
        """
        result = self.execute_query(
            f"DESCRIBE {catalog}.{schema}.{table}", 
            catalog=catalog, 
            schema=schema
        )
        columns = []
        
        for row in result.rows:
            columns.append({
                "name": row[0],
                "type": row[1],
                "extra": row[2] if len(row) > 2 else None,
                "catalog": catalog,
                "schema": schema,
                "table": table
            })
            
        return columns
    
    def get_table_details(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """
        Get detailed information about a table including columns and statistics.
        
        Args:
            catalog: The catalog name.
            schema: The schema name.
            table: The table name.
            
        Returns:
            Dict[str, Any]: Detailed table information.
        """
        columns = self.get_columns(catalog, schema, table)
        
        # Get table statistics if available (might not be supported by all connectors)
        try:
            stats_query = f"""
            SELECT * FROM {catalog}.information_schema.tables
            WHERE table_catalog = '{catalog}'
            AND table_schema = '{schema}'
            AND table_name = '{table}'
            """
            stats_result = self.execute_query(stats_query, catalog=catalog)
            stats = {}
            
            if stats_result.rows:
                row = stats_result.rows[0]
                for i, col in enumerate(stats_result.columns):
                    stats[col.lower()] = row[i]
        except Exception as e:
            logger.warning(f"Failed to get table statistics: {e}")
            stats = {}
            
        return {
            "name": table,
            "catalog": catalog,
            "schema": schema,
            "columns": columns,
            "statistics": stats
        }
    
    def cancel_query(self, query_id: str) -> bool:
        """
        Cancel a running query.
        
        Args:
            query_id: The ID of the query to cancel.
            
        Returns:
            bool: True if the query was successfully canceled, False otherwise.
        """
        self.ensure_connection()
        
        try:
            # Use system procedures to cancel the query
            self.execute_query(f"CALL system.runtime.kill_query(query_id => '{query_id}')")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel query {query_id}: {e}")
            return False
