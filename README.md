# Trino MCP Server

Model Context Protocol server for Trino, providing AI models with structured access to Trino's distributed SQL query engine.

## Features

- Exposes Trino resources through MCP protocol
- Enables AI tools to query and analyze data in Trino
- Supports both WebSockets and SSE transports
- Fixed catalog handling for proper Trino query execution

## Usage

```bash
# Start the server with docker-compose
docker-compose up -d
```

The server will be available at:
- Trino: http://localhost:9095
- MCP server: http://localhost:9096

## Transport Options

This server supports two transport methods:

### STDIO Transport (Recommended)

STDIO transport works reliably and is the recommended method for testing and development:

```bash
# Run with STDIO transport inside the container
docker exec -i trino_mcp_trino-mcp_1 python -m trino_mcp.server --transport stdio --debug --trino-host trino --trino-port 8080 --trino-user trino --trino-catalog memory
```

### SSE Transport (Default but has issues)

SSE is the default transport but has known issues with MCP 1.3.0:

```bash
# Run with SSE transport (with potential connection issues)
docker exec trino_mcp_trino-mcp_1 python -m trino_mcp.server --transport sse --host 0.0.0.0 --port 8000 --debug
```

## Known Issues

### MCP 1.3.0 SSE Issues

There's a known issue with MCP 1.3.0's SSE transport that causes server crashes when clients disconnect. This is why we recommend using STDIO transport instead. The error manifests as:

```
RuntimeError: generator didn't stop after athrow()
anyio.BrokenResourceError
```

### Trino Catalog Handling

We fixed an issue with catalog handling in the Trino client. The original implementation attempted to use `USE catalog` statements, which don't work reliably. The fix directly sets the catalog in the connection parameters.

## Project Structure

This project is organized as follows:

- `src/` - Main source code for the Trino MCP server
- `examples/` - Simple examples showing how to use the server
- `scripts/` - Useful diagnostic and testing scripts
- `tools/` - Utility scripts for data creation and setup
- `tests/` - Automated tests

Key files:
- `test_mcp_stdio.py` - Main test script using STDIO transport (recommended)
- `run_tests.sh` - Script to run automated tests
- `examples/simple_mcp_query.py` - Simple example to query data using MCP

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run automated tests 
./run_tests.sh

# Test MCP with STDIO transport (recommended)
python test_mcp_stdio.py

# Simple example query
python examples/simple_mcp_query.py "SELECT 'Hello World' AS message"
```

## Testing

To test that Trino queries are working correctly, use the STDIO transport test script:

```bash
# Recommended test method (STDIO transport)
python test_mcp_stdio.py
```

This script demonstrates end-to-end flow including:
1. Initializing the MCP connection
2. Listing available tools
3. Executing queries against Trino
4. Handling errors appropriately

For SSE transport testing (may have connection issues with MCP 1.3.0):
```bash
# Alternative test method (SSE transport)
python scripts/test_messages.py
```

## License

Apache License 2.0
