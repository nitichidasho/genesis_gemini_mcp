"""Minimal MCP server test."""

import sys
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    logger.debug("Importing FastMCP")
    from mcp.server.fastmcp import FastMCP
    logger.debug("Successfully imported FastMCP")

    logger.debug("Creating FastMCP instance")
    app = FastMCP("Test Server")
    logger.debug("Successfully created FastMCP instance")

    @app.tool()
    def hello_world() -> str:
        """Return a greeting."""
        logger.debug("hello_world tool called")
        return "Hello, world!"

    if __name__ == "__main__":
        logger.debug("Starting server")
        app.run()
except Exception as e:
    logger.exception("Error in MCP server:")
    sys.exit(1) 