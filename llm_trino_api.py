#!/usr/bin/env python3
"""
Simple FastAPI server that lets LLMs query Trino through MCP via a REST API.

Run with:
  pip install fastapi uvicorn
  uvicorn llm_trino_api:app --reload

This creates a REST API endpoint at:
  http://localhost:8000/query

Example curl:
  curl -X POST "http://localhost:8000/query" \\
       -H "Content-Type: application/json" \\
       -d '{"query": "SELECT * FROM memory.bullshit.real_bullshit_data LIMIT 3"}'
"""
import fastapi
import pydantic
from llm_query_trino import query_trino, format_results
from typing import Optional, Dict, Any

# Create FastAPI app
app = fastapi.FastAPI(
    title="Trino MCP API for LLMs",
    description="Simple API to query Trino via MCP protocol for LLMs",
    version="0.1.0"
)

# Define request model
class QueryRequest(pydantic.BaseModel):
    query: str
    catalog: str = "memory"
    schema: Optional[str] = "bullshit"
    explain: bool = False

# Define response model
class QueryResponse(pydantic.BaseModel):
    success: bool
    message: str
    results: Optional[Dict[str, Any]] = None
    formatted_results: Optional[str] = None

@app.post("/query", response_model=QueryResponse)
async def trino_query(request: QueryRequest):
    """
    Execute a SQL query against Trino via MCP and return results.
    
    Example:
    ```json
    {
        "query": "SELECT * FROM memory.bullshit.real_bullshit_data LIMIT 3",
        "catalog": "memory",
        "schema": "bullshit"
    }
    ```
    """
    try:
        # If explain mode is on, add EXPLAIN to the query
        query = request.query
        if request.explain:
            query = f"EXPLAIN {query}"
            
        # Execute the query
        results = query_trino(query, request.catalog, request.schema)
        
        # Check for errors
        if "error" in results:
            return QueryResponse(
                success=False,
                message=f"Query execution failed: {results['error']}",
                results=results
            )
        
        # Format results for human readability
        formatted_results = format_results(results)
        
        return QueryResponse(
            success=True,
            message="Query executed successfully",
            results=results,
            formatted_results=formatted_results
        )
    
    except Exception as e:
        return QueryResponse(
            success=False,
            message=f"Error executing query: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint with usage instructions."""
    return {
        "message": "Trino MCP API for LLMs",
        "usage": "POST to /query with JSON body containing 'query', 'catalog' (optional), and 'schema' (optional)",
        "example": {
            "query": "SELECT * FROM memory.bullshit.real_bullshit_data LIMIT 3",
            "catalog": "memory",
            "schema": "bullshit"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 