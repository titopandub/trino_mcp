"""
Main module for the Trino MCP server.
"""
from __future__ import annotations

import argparse
import json
import sys
import os
import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, Response, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
from mcp.server.fastmcp import Context, FastMCP

from trino_mcp.config import ServerConfig, TrinoConfig
from trino_mcp.resources import register_trino_resources
from trino_mcp.tools import register_trino_tools
from trino_mcp.trino_client import TrinoClient

# Global app context for health check access
app_context_global = None

@dataclass
class AppContext:
    """Application context passed to all MCP handlers."""
    trino_client: TrinoClient
    config: ServerConfig
    is_healthy: bool = True

# Models for the LLM API
class QueryRequest(BaseModel):
    """Model for query requests."""
    query: str
    catalog: str = "memory"
    schema: Optional[str] = None
    explain: bool = False

class QueryResponse(BaseModel):
    """Model for query responses."""
    success: bool
    message: str
    results: Optional[Dict[str, Any]] = None

@asynccontextmanager
async def app_lifespan(mcp: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manage the application lifecycle.
    
    Args:
        mcp: The MCP server instance.
        
    Yields:
        AppContext: The application context with initialized services.
    """
    global app_context_global
    
    logger.info("Initializing Trino MCP server")
    
    # Get server configuration from environment or command line
    config = parse_args()
    
    # Initialize Trino client
    trino_client = TrinoClient(config.trino)
    
    # Create and set global app context
    app_context = AppContext(trino_client=trino_client, config=config)
    app_context_global = app_context
    
    try:
        # Connect to Trino
        logger.info(f"Connecting to Trino at {config.trino.host}:{config.trino.port}")
        trino_client.connect()
        
        # Register resources and tools
        logger.info("Registering resources and tools")
        register_trino_resources(mcp, trino_client)
        register_trino_tools(mcp, trino_client)
        
        # Yield the application context
        logger.info("Trino MCP server initialized and ready")
        yield app_context
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        app_context.is_healthy = False
        yield app_context
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Trino MCP server")
        if trino_client.conn:
            trino_client.disconnect()
        app_context.is_healthy = False


def parse_args() -> ServerConfig:
    """
    Parse command line arguments and return server configuration.
    
    Returns:
        ServerConfig: The server configuration.
    """
    parser = argparse.ArgumentParser(description="Trino MCP server")
    
    # Server configuration
    parser.add_argument("--name", default="Trino MCP", help="Server name")
    parser.add_argument("--version", default="0.1.0", help="Server version")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="Transport type")
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP server (SSE transport only)")
    parser.add_argument("--port", type=int, default=3000, help="Port for HTTP server (SSE transport only)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Trino connection
    parser.add_argument("--trino-host", default="localhost", help="Trino host")
    parser.add_argument("--trino-port", type=int, default=8080, help="Trino port")
    parser.add_argument("--trino-user", default="trino", help="Trino user")
    parser.add_argument("--trino-password", help="Trino password")
    parser.add_argument("--trino-catalog", help="Default Trino catalog")
    parser.add_argument("--trino-schema", help="Default Trino schema")
    parser.add_argument("--trino-http-scheme", default="http", help="Trino HTTP scheme")
    
    args = parser.parse_args()
    
    # Create Trino configuration
    trino_config = TrinoConfig(
        host=args.trino_host,
        port=args.trino_port,
        user=args.trino_user,
        password=args.trino_password,
        catalog=args.trino_catalog,
        schema=args.trino_schema,
        http_scheme=args.trino_http_scheme
    )
    
    # Create server configuration
    server_config = ServerConfig(
        name=args.name,
        version=args.version,
        transport_type=args.transport,
        host=args.host,
        port=args.port,
        debug=args.debug,
        trino=trino_config
    )
    
    return server_config


def create_app() -> FastMCP:
    """
    Create and configure the MCP server application.
    
    Returns:
        FastMCP: The configured MCP server.
    """
    # Create the MCP server with lifespan management
    mcp = FastMCP(
        "Trino MCP",
        dependencies=["trino>=0.329.0"],
        lifespan=app_lifespan
    )
    
    return mcp


def create_health_app() -> FastAPI:
    """
    Create a FastAPI app that provides a health check endpoint and LLM API.
    
    This function creates a FastAPI app with a health check endpoint and
    a query endpoint for LLMs to use.
    
    Returns:
        FastAPI: The FastAPI app with health check and LLM API endpoints.
    """
    app = FastAPI(
        title="Trino MCP API",
        description="API for health checks and LLM query access to Trino MCP",
        version="0.1.0"
    )
    
    @app.get("/health")
    async def health():
        global app_context_global
        
        # For Docker health check, always return 200 during startup
        # This gives the app time to initialize
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "message": "Health check endpoint is responding"}
        )
    
    @app.post("/api/query", response_model=QueryResponse)
    async def query(request: QueryRequest):
        """
        Execute a SQL query against Trino and return results.
        
        This endpoint is designed to be used by LLMs to query Trino through MCP.
        """
        global app_context_global
        
        if not app_context_global or not app_context_global.is_healthy:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": "Trino MCP server is not healthy or not initialized"
                }
            )
            
        logger.info(f"LLM API Query: {request.query}")
        
        try:
            # Use the Trino client from the app context
            client = app_context_global.trino_client
            
            # Optionally add EXPLAIN
            query = request.query
            if request.explain:
                query = f"EXPLAIN {query}"
                
            # Execute the query
            result = client.execute_query(query, request.catalog, request.schema)
            
            # Format the results for the response
            formatted_rows = []
            for row in result.rows:
                # Convert row to dict using column names
                row_dict = {}
                for i, col in enumerate(result.columns):
                    row_dict[col] = row[i]
                formatted_rows.append(row_dict)
                
            return {
                "success": True,
                "message": "Query executed successfully",
                "results": {
                    "query_id": result.query_id,
                    "columns": result.columns,
                    "rows": formatted_rows,
                    "row_count": result.row_count,
                    "execution_time_ms": result.query_time_ms
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Error executing query: {str(e)}"
                }
            )
    
    @app.get("/api")
    async def api_root():
        """Root API endpoint with usage instructions."""
        return {
            "message": "Trino MCP API for LLMs",
            "version": app_context_global.config.version if app_context_global else "unknown",
            "endpoints": {
                "health": "GET /health - Check server health",
                "query": "POST /api/query - Execute SQL queries"
            },
            "query_example": {
                "query": "SELECT * FROM memory.bullshit.real_bullshit_data LIMIT 3",
                "catalog": "memory",
                "schema": "bullshit"
            }
        }
    
    return app


def main() -> None:
    """
    Main entry point for the server.
    """
    config = parse_args()
    mcp = create_app()
    
    # ADDING EXPLICIT CONTEXT INITIALIZATION HERE
    global app_context_global
    try:
        # Initialize the Trino client
        logger.info(f"Connecting to Trino at {config.trino.host}:{config.trino.port}")
        trino_client = TrinoClient(config.trino)
        trino_client.connect()
        
        # Create application context
        app_context = AppContext(
            trino_client=trino_client,
            config=config,
            is_healthy=True
        )
        
        # Set global context
        app_context_global = app_context
        
        # Register resources and tools
        register_trino_resources(mcp, trino_client)
        register_trino_tools(mcp, trino_client)
        
        logger.info("Trino MCP server initialized and ready")
    except Exception as e:
        logger.error(f"Error initializing Trino MCP: {e}")
        if app_context_global:
            app_context_global.is_healthy = False
    
    if config.transport_type == "stdio":
        # For STDIO transport, run directly
        logger.info("Starting Trino MCP server with STDIO transport")
        mcp.run()
    else:
        # For SSE transport, use run_sse_async method from MCP library
        logger.info(f"Starting Trino MCP server with SSE transport on {config.host}:{config.port}")
        
        # In MCP 1.3.0, run_sse_async takes no arguments
        # We set the environment variables to configure the host and port
        os.environ["MCP_HOST"] = config.host
        os.environ["MCP_PORT"] = str(config.port)
        
        # Configure more robust error handling for the server
        import traceback
        try:
            # Try to import and configure SSE settings if available in this version
            from mcp.server.sse import configure_sse
            configure_sse(ignore_client_disconnect=True)
            logger.info("Configured SSE with ignore_client_disconnect=True")
        except (ImportError, AttributeError):
            logger.warning("Could not configure SSE settings - this may be expected in some MCP versions")
        
        # Start a separate thread for the health check endpoint
        import threading
        
        def run_health_check():
            """Run the health check FastAPI app."""
            health_app = create_health_app()
            # Use a different port for the health check endpoint
            health_port = config.port + 1
            logger.info(f"Starting API server on port {health_port}")
            uvicorn.run(health_app, host=config.host, port=health_port)
        
        # Start the health check in a separate thread
        health_thread = threading.Thread(target=run_health_check)
        health_thread.daemon = True
        health_thread.start()
        
        # Now run the SSE server with robust error handling
        try:
            asyncio.run(mcp.run_sse_async())
        except RuntimeError as e:
            if "generator didn't stop after athrow()" in str(e):
                logger.error(f"Generator error in SSE server. This is a known issue with MCP 1.3.0: {e}")
                
                # Set unhealthy status for health checks
                if app_context_global:
                    app_context_global.is_healthy = False
                
                logger.info("Server will continue running but may not function correctly.")
                
                # Keep the server alive despite the error
                import time
                while True:
                    time.sleep(60)  # Sleep to keep the container running
                    
            else:
                logger.error(f"Fatal error running SSE server: {e}")
                logger.error(traceback.format_exc())
                raise
        except Exception as e:
            logger.error(f"Fatal error running SSE server: {e}")
            logger.error(traceback.format_exc())
            raise


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    main()
