# Trino MCP Server

Model Context Protocol server for Trino, providing AI models with structured access to Trino's distributed SQL query engine.

⚠️ **EARLY DEVELOPMENT STAGE (v0.1)** ⚠️  
This project is in early development with many features still being implemented and tested. Feel free to fork and contribute! Use accordingly.

## Features

- Exposes Trino resources through MCP protocol
- Enables AI tools to query and analyze data in Trino
- Provides transport options (STDIO transport works reliably; SSE transport has serious issues)
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

This server supports two transport methods, but only STDIO is currently reliable:

### STDIO Transport (Recommended and Working)

STDIO transport works reliably and is currently the only recommended method for testing and development:

```bash
# Run with STDIO transport inside the container
docker exec -i trino_mcp_trino-mcp_1 python -m trino_mcp.server --transport stdio --debug --trino-host trino --trino-port 8080 --trino-user trino --trino-catalog memory
```

### SSE Transport (NOT RECOMMENDED - Has Critical Issues)

SSE is the default transport in MCP but has serious issues with the current MCP 1.3.0 version, causing server crashes on client disconnections. **Not recommended for use until these issues are resolved**:

```bash
# NOT RECOMMENDED: Run with SSE transport (crashes on disconnection)
docker exec trino_mcp_trino-mcp_1 python -m trino_mcp.server --transport sse --host 0.0.0.0 --port 8000 --debug
```

## Known Issues

### MCP 1.3.0 SSE Transport Crashes

There's a critical issue with MCP 1.3.0's SSE transport that causes server crashes when clients disconnect. Until a newer MCP version is integrated, use STDIO transport exclusively. The error manifests as:

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

**IMPORTANT**: All scripts must be run in the context of the Docker environment, as they connect to services inside the Docker network at this time.

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run automated tests (against the Docker container)
./run_tests.sh

# Test MCP using STDIO transport (requires Docker running)
python test_mcp_stdio.py

# Simple example query (requires Docker running)
python examples/simple_mcp_query.py "SELECT 'Hello World' AS message"
```

## Testing

To test that Trino queries are working correctly, use the STDIO transport test script:

```bash
# Recommended test method (STDIO transport)
# Requires Docker containers to be running
python test_mcp_stdio.py
```

This script demonstrates end-to-end flow including:
1. Initializing the MCP connection
2. Listing available tools
3. Executing queries against Trino
4. Handling errors appropriately

For SSE transport testing (currently broken with MCP 1.3.0):
```bash
# DO NOT USE until MCP SSE issues are fixed
python scripts/test_messages.py
```

## Future Work

This is an early v0.1 version with many planned improvements:

- [ ] Integrate with newer MCP versions when available to fix SSE transport issues
- [ ] Add/Validate support for Hive, JDBC, and other connectors
- [ ] Add more comprehensive query validation across different types and complexities
- [ ] Implement support for more data types and advanced Trino features
- [ ] Improve error handling and recovery mechanisms
- [ ] Add user authentication and permission controls
- [ ] Create more comprehensive examples and documentation
- [ ] Develop admin monitoring and management interfaces
- [ ] Add performance metrics and query optimization hints
- [ ] Implement support for long-running queries and result streaming

## License

Apache License 2.0
