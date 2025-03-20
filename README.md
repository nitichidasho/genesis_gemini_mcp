<img src="imgs/big_text.png" alt="Genesis" width="200" />

# Genesis MCP Server

A Model Context Protocol (MCP) server for Genesis World simulations with visualization support.

## Quick Start

For the fastest way to get started with visualization:

```bash
# Run the simplified setup script (only installs what's needed)
./setup.sh

# Run the stdio client (opens a visualization window)
./examples/stdio_client.py
```

This will directly start a Genesis World simulation with visualization using stdio transport.

## Transport Method: stdio

This server uses **stdio transport** which is required for Genesis World visualization features.
The visualization components require a local runtime and cannot work over network transports.

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

````bash
# Run with stdio transport (required for visualization)
./start.sh


### Using with the MCP Inspector

To use with the MCP Inspector for debugging:

```bash
# In one terminal, start the inspector
mcp-inspector

# In another terminal, start the server with stdio transport
python server.py
````

Configure the MCP Inspector with:

- Transport Type: STDIO
- Command: python
- Arguments: server.py

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

## MCP Client

The repository includes stdio client for visualization:

```bash
# Run a simulation with Genesis World visualization
./examples/stdio_client.py
```

Happy hacking!
