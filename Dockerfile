FROM python:3.11-slim

WORKDIR /app

# Install Node.js for MCP Inspector
RUN apt-get update && \
  apt-get install -y curl && \
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
  apt-get install -y nodejs && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Install MCP Inspector
RUN npm install -g @modelcontextprotocol/inspector@0.6.0

# Install uv for better dependency management
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir uv

# Copy pyproject.toml first for better caching
COPY pyproject.toml ./

# Generate requirements.lock from pyproject.toml
RUN uv pip compile pyproject.toml -o requirements.lock --no-deps

# Install all dependencies directly without using virtual env
RUN pip install --no-cache-dir -r requirements.lock
RUN pip install --no-cache-dir genesis==0.2.1 --no-deps
RUN pip install --no-cache-dir "mcp[cli]==1.4.1"

# Copy the application code
COPY . .

# Install the package in development mode
RUN pip install --no-cache-dir -e .

# Verify mcp is in PATH
RUN which mcp || echo "mcp not found in PATH"

# Create a startup script that runs both services properly
RUN echo '#!/bin/bash\n\
  set -e\n\
  \n\
  # Handle SIGTERM and SIGINT to gracefully shut down both services\n\
  function cleanup() {\n\
  echo "Shutting down services..."\n\
  if [ ! -z "$MCP_INSPECTOR_PID" ]; then\n\
  echo "Stopping MCP Inspector (PID: $MCP_INSPECTOR_PID)"\n\
  kill -TERM $MCP_INSPECTOR_PID 2>/dev/null || true\n\
  fi\n\
  if [ ! -z "$MCP_SERVER_PID" ]; then\n\
  echo "Stopping MCP Server (PID: $MCP_SERVER_PID)"\n\
  kill -TERM $MCP_SERVER_PID 2>/dev/null || true\n\
  fi\n\
  exit 0\n\
  }\n\
  \n\
  trap cleanup SIGTERM SIGINT\n\
  \n\
  echo "Starting MCP Inspector..."\n\
  # Set environment variables to make Inspector accessible from outside\n\
  export HOST=0.0.0.0\n\
  export CLIENT_HOST=0.0.0.0\n\
  export CLIENT_PORT=5173\n\
  export SERVER_PORT=3000\n\
  export PUBLIC_HOSTNAME=${PUBLIC_HOSTNAME:-0.0.0.0}\n\
  \n\
  # Start MCP Inspector with its own HTTP server instead of stdio\n\
  mcp-inspector &\n\
  MCP_INSPECTOR_PID=$!\n\
  \n\
  echo "MCP Inspector started with PID $MCP_INSPECTOR_PID"\n\
  echo "MCP Inspector UI should be available at http://$PUBLIC_HOSTNAME:5173"\n\
  \n\
  echo "Starting MCP Server..."\n\
  /usr/local/bin/mcp run server.py &\n\
  MCP_SERVER_PID=$!\n\
  \n\
  echo "MCP Server started with PID $MCP_SERVER_PID"\n\
  \n\
  # Keep the container running\n\
  echo "Services are running. Press Ctrl+C to stop."\n\
  wait $MCP_SERVER_PID $MCP_INSPECTOR_PID\n\
  ' > /app/start.sh && \
  chmod +x /app/start.sh

# Expose ports: 
# - 8000: MCP server
# - 5173: MCP Inspector client UI
# - 3000: MCP Inspector proxy server
EXPOSE 8000 5173 3000

# Command to run the application
CMD ["/app/start.sh"]