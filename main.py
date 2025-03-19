import uvicorn
from src.genesis_mcp.server import create_app

def main():
    """Start the Genesis World MCP server."""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
