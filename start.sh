#!/bin/bash
# Script to start the Genesis MCP server with stdio transport

# Activate the virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set transport to stdio
export MCP_TRANSPORT=stdio

# Run the server with stdio transport
python server.py

# Note: With stdio transport, the server will communicate directly
# with the client through standard input/output, so this script
# is typically not run directly but used by the client. 