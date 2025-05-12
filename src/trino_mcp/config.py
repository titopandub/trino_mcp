"""
Configuration module for the Trino MCP server.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TrinoConfig:
    """Configuration for the Trino connection."""
    host: str = "localhost"
    port: int = 8080
    user: str = "trino"
    password: Optional[str] = None
    catalog: Optional[str] = None
    schema: Optional[str] = None
    http_scheme: str = "http"
    auth: Optional[Any] = None
    max_attempts: int = 3
    request_timeout: float = 30.0
    http_headers: Dict[str, str] = field(default_factory=dict)
    verify: bool = True

    @property
    def connection_params(self) -> Dict[str, Any]:
        """Return connection parameters for the Trino client."""
        params = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "catalog": self.catalog,
            "http_scheme": self.http_scheme,
            "max_attempts": self.max_attempts,
            "request_timeout": self.request_timeout,
            "verify": self.verify,
        }
        
        if self.password:
            params["password"] = self.password
        
        if self.auth:
            params["auth"] = self.auth
            
        if self.http_headers:
            params["http_headers"] = self.http_headers
            
        return params


@dataclass
class ServerConfig:
    """Configuration for the MCP server."""
    name: str = "Trino MCP"
    version: str = "0.1.0"
    transport_type: str = "stdio"  # "stdio" or "sse"
    host: str = "127.0.0.1"
    port: int = 3000
    debug: bool = False
    trino: TrinoConfig = field(default_factory=TrinoConfig)


def load_config_from_env() -> ServerConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        ServerConfig: The server configuration.
    """
    # This would normally load from environment variables or a config file
    # For now, we'll just return the default config
    return ServerConfig()
