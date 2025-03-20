#!/bin/bash
set -e

echo "Setting up Genesis MCP environment..."

# Check Python version
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Error: Python 3 is required but not found"
    exit 1
fi

# Verify Python version is at least 3.8
PYTHON_VERSION=$($PYTHON --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "Error: Python 3.8+ is required, found $PYTHON_VERSION"
    exit 1
fi

# Check for ffmpeg installation
echo "Checking for ffmpeg..."
if ! command -v ffmpeg &>/dev/null; then
    echo "ffmpeg not found. Attempting to install..."
    if [[ "$(uname -s)" == "Darwin" ]]; then
        # macOS - try to use brew if available
        if command -v brew &>/dev/null; then
            brew install ffmpeg
        else
            echo "Warning: Homebrew not found. Please install ffmpeg manually:"
            echo "  1. Install Homebrew: https://brew.sh/"
            echo "  2. Run: brew install ffmpeg"
        fi
    elif [[ "$(uname -s)" == "Linux" ]]; then
        # Linux - try apt-get for Debian/Ubuntu based distros
        if command -v apt-get &>/dev/null; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        # Try dnf for Fedora/RHEL based distros
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y ffmpeg
        else
            echo "Warning: Could not determine package manager. Please install ffmpeg manually."
        fi
    else
        echo "Warning: Unsupported OS. Please install ffmpeg manually."
    fi
else
    echo "ffmpeg is already installed."
fi

# Check for uv package manager
if ! command -v uv &>/dev/null; then
    echo "Installing uv package manager..."
    $PYTHON -m pip install uv
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
else
    echo "Using existing virtual environment..."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install PyTorch (required by genesis-world)
echo "Installing PyTorch (required by genesis-world)..."
if [[ "$(uname -s)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
    # Apple Silicon macOS
    uv pip install torch torchvision torchaudio
else
    # For other platforms (Linux, Intel macOS)
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Uninstall pygel3d to avoid conflict with taichi
echo "Uninstalling pygel3d to avoid conflict with taichi..."
uv pip uninstall -y pygel3d

# Install mcp package without dependencies
echo "Installing mcp package without dependencies..."
uv pip install "mcp[cli]==1.4.1" --no-deps

# Install mcp dependencies except pydantic (which is already installed via genesis-mcp)
echo "Installing mcp dependencies except pydantic..."
uv pip install anyio httpx httpx-sse pydantic-settings sse-starlette "starlette<0.39.0,>=0.37.2" uvicorn

# Install optional MCP Inspector
if command -v npm &>/dev/null; then
    echo "Installing MCP Inspector using Taobao npm registry for faster installation in China..."
    npm install -g @modelcontextprotocol/inspector@0.6.0 --registry=https://registry.npmmirror.com
else
    echo "npm not found, skipping MCP Inspector installation"
fi

echo
echo "Setup completed successfully!"
echo
echo "To activate the virtual environment:"
echo "source .venv/bin/activate"
echo
echo "To start the server with stdio transport (for visualization):"
echo "./start.sh"
echo
echo "To run a sample client with visualization:"
echo "./examples/stdio_client.py"