#!/bin/bash
set -e

# Handle SIGTERM and SIGINT to gracefully shut down both services
function cleanup() {
  echo "Shutting down services..."
  if [ ! -z "$MCP_INSPECTOR_PID" ]; then
    echo "Stopping MCP Inspector (PID: $MCP_INSPECTOR_PID)"
    kill -TERM $MCP_INSPECTOR_PID 2>/dev/null || true
  fi
  if [ ! -z "$MCP_SERVER_PID" ]; then
    echo "Stopping MCP Server (PID: $MCP_SERVER_PID)"
    kill -TERM $MCP_SERVER_PID 2>/dev/null || true
  fi
  exit 0
}

trap cleanup SIGTERM SIGINT

echo "Starting MCP Inspector..."
# Set environment variables to make Inspector accessible from outside
export HOST=0.0.0.0
export CLIENT_HOST=0.0.0.0
export CLIENT_PORT=5173
export SERVER_PORT=3000
export PUBLIC_HOSTNAME=${PUBLIC_HOSTNAME:-0.0.0.0}

# Start MCP Inspector with its own HTTP server
mcp-inspector &
MCP_INSPECTOR_PID=$!

echo "MCP Inspector started with PID $MCP_INSPECTOR_PID"
echo "MCP Inspector UI should be available at http://$PUBLIC_HOSTNAME:5173"

echo "Starting MCP Server..."
/usr/local/bin/mcp run server.py &
MCP_SERVER_PID=$!

echo "MCP Server started with PID $MCP_SERVER_PID"

# Keep the container running
echo "Services are running. Press Ctrl+C to stop."
wait $MCP_SERVER_PID $MCP_INSPECTOR_PID