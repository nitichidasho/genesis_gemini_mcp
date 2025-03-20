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

# Copy requirements first for better caching
COPY pyproject.toml .

# Install dependencies
RUN pip install --upgrade pip && \
  pip install hatchling && \
  pip install pydantic==2.7.2 && \
  pip install "mcp[cli]==1.4.1" && \
  pip install genesis==0.2.1 --no-deps

# Copy project files
COPY . .

# Install the project
RUN pip install -e .

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0
ENV INSPECTOR_PORT=5173
ENV INSPECTOR_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Expose ports for MCP server and Inspector
EXPOSE 8000
EXPOSE 5173

# Start the MCP Inspector in background and the MCP server
CMD mcp-inspector --port $INSPECTOR_PORT --address $INSPECTOR_HOST & python server.py