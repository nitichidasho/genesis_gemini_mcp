#!/bin/bash
set -e

echo "Setting up Genesis MCP environment using lock file..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv package manager is not installed."
    echo "Install it with: pip install uv"
    exit 1
fi

# Remove uv.lock if it exists to avoid conflicts with mcp dev
if [ -f "uv.lock" ]; then
    echo "Removing uv.lock to avoid conflicts with mcp dev..."
    rm uv.lock
fi

# Force recreate the virtual environment to ensure it's clean
echo "Creating fresh virtual environment with uv..."
rm -rf .venv
uv venv .venv

# Ensure proper activation by using the absolute path
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    source "$(pwd)/.venv/bin/activate"
else
    source "$(pwd)/.venv/Scripts/activate"
fi

# Verify Python interpreter is working
echo "Verifying Python interpreter..."
which python3 || which python

# Create requirements.lock if it doesn't exist
if [ ! -f "requirements.lock" ]; then
    echo "Creating requirements.lock from pyproject.toml..."
    uv pip compile pyproject.toml -o requirements.lock
fi

# Install from the lock file
echo "Installing dependencies from lock file..."
uv pip install -r requirements.lock

# Install genesis without dependencies
echo "Installing genesis without dependencies..."
uv pip install genesis==0.2.1 --no-deps

# Install the package in development mode
echo "Installing the package in development mode..."
uv pip install -e .

# Check if npm is installed (for MCP Inspector)
if command -v npm &> /dev/null; then
    echo "Installing MCP Inspector..."
    npm install -g @modelcontextprotocol/inspector@0.6.0
else
    echo "WARNING: npm not found. MCP Inspector will not be installed."
    echo "You can install it manually with: npm install -g @modelcontextprotocol/inspector@0.6.0"
fi

echo
echo "Setup completed successfully!"
echo
echo "To activate the virtual environment:"
echo "source $(pwd)/.venv/bin/activate"
echo
echo "To start the server:"
echo "mcp run server.py"
echo
echo "Happy hacking!"