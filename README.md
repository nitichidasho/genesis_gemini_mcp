<img src="imgs/big_text.png" alt="Genesis" width="200" />

# Genesis MCP Server

A Model Context Protocol (MCP) server for Genesis World simulations.

## Setup

### Prerequisites

- Python 3.8+
- uv package manager (`pip install uv`)
- npm (optional, for MCP Inspector)

### Installation

#### Linux/macOS

```bash
# Clone the repository
git clone https://github.com/username/genesis-mcp.git
cd genesis-mcp

# Run the setup script
./setup.sh

# Activate the virtual environment
source .venv/bin/activate
```

#### Windows

```powershell
# Clone the repository
git clone https://github.com/username/genesis-mcp.git
cd genesis-mcp

# Run the setup script
setup.bat

# Activate the virtual environment
.venv\Scripts\activate.bat
```

### Manual Installation with uv

If you prefer to install dependencies manually:

1. Create a virtual environment:

   ```bash
   uv venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate.bat  # Windows
   ```

2. Install dependencies from lock file:

   ```bash
   uv pip install -r requirements.lock
   uv pip install -e .
   uv pip install genesis==0.2.1 --no-deps
   ```

3. Install MCP Inspector (optional):
   ```bash
   npm install -g @modelcontextprotocol/inspector@0.6.0
   ```

## Running the Server

Start the MCP server:

```bash
mcp run server.py
```

To use with the MCP Inspector for debugging:

```bash
# In one terminal
mcp-inspector

# In another terminal
mcp run server.py
```

### Using MCP Inspector with uv

If you're using uv and want to run with the MCP Inspector, configure the inspector with:

- Transport Type: STDIO
- Command: uv
- Arguments: run --with mcp mcp run server.py

## Available Resources

### World Info

Get information about Genesis World features:

```
world_info://{name}
```

## Available Tools

### Run Simulation

Run a Genesis World simulation with provided code and parameters:

```
run_simulation
```

## Available Prompts

### Basic Simulation

Generate a basic simulation script based on specified world size and agent count:

```
basic_simulation
```

## Development

To run tests:

```bash
pytest
```

## Docker

To build and run with Docker:

```bash
docker build -t genesis-mcp .
docker run -p 8000:8000 genesis-mcp
```

Happy hacking!
