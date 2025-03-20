#!/usr/bin/env python3
"""Genesis MCP client using stdio transport."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def main():
    # Start the server process with stdio transport
    print("Starting Genesis MCP server with stdio transport...")
    server_process = subprocess.Popen(
        ["python", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Create an MCP session with stdio transport
    async with stdio_client(
        StdioServerParameters(command="uv", args=["run", "server.py"])
    ) as (read, write):
          async with ClientSession(read, write) as session:
            await session.initialize()
            # List available tools
            print("Available tools:", session.list_tools())
            
            # Read the genesis_example.py file
            example_path = Path("examples/genesis_example.py")
            if example_path.exists():
                with open(example_path, "r") as f:
                    code = f.read()
                
                # Run the simulation
                print("Running Genesis World simulation...")
                result = session.call_tool(
                    "run_simulation",
                    inputs={"code": code, "parameters": {}}
                )
                print("Simulation complete!", result)
                
            else:
                print(f"Error: Could not find example file at {example_path}")
                    
asyncio.run(main())