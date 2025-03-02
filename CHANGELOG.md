# Changelog

## v0.1.1 (2023-05-17)

### 🐛 Bug Fixes

- **Fixed Trino client catalog handling**: The Trino client now correctly sets the catalog in connection parameters instead of using unreliable `USE catalog` statements.
- **Improved query execution**: Queries now correctly execute against specified catalogs.
- **Added error handling**: Better error handling for catalog and schema operations.

### 📝 Documentation 

- Added detailed documentation about transport options and known issues.
- Created test scripts demonstrating successful MCP-Trino interaction.
- Documented workarounds for MCP 1.3.0 SSE transport issues.

### 🧪 Testing

- Added `test_mcp_stdio.py` for testing MCP with STDIO transport.
- Added catalog connection testing scripts and diagnostics.

### 🚧 Known Issues

- MCP 1.3.0 SSE transport has issues with client disconnection.
- Use STDIO transport for reliable operation until upgrading to a newer MCP version. 