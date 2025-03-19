"""Example client for Genesis World MCP Server."""

import json
import sys
from typing import Dict, Any

import requests

MCP_SERVER_URL = "http://localhost:8000/mcp"


def run_simulation(code: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run a simulation via the MCP server.
    
    Args:
        code: The Genesis World simulation code to run
        parameters: Optional parameters for the simulation
        
    Returns:
        The result of the simulation
    """
    request_data = {
        "request_id": "client-sim-request",
        "request_type": "run_simulation",
        "inputs": {
            "code": code,
            "parameters": parameters or {}
        }
    }
    
    response = requests.post(MCP_SERVER_URL, json=request_data)
    response.raise_for_status()
    
    result = response.json()
    
    if result["status"] == "error":
        print(f"Error: {result['error_message']}")
        return {}
    
    return result["outputs"]


def get_world_info() -> Dict[str, Any]:
    """Get information about Genesis World from the MCP server.
    
    Returns:
        Information about available Genesis World features
    """
    request_data = {
        "request_id": "client-info-request",
        "request_type": "get_world_info",
        "inputs": {}
    }
    
    response = requests.post(MCP_SERVER_URL, json=request_data)
    response.raise_for_status()
    
    result = response.json()
    
    if result["status"] == "error":
        print(f"Error: {result['error_message']}")
        return {}
    
    return result["outputs"]["world_info"]


def print_pretty_json(data: Dict) -> None:
    """Print a dictionary as pretty JSON."""
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    # Simple example demonstrating the MCP client usage
    
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        print("Getting Genesis World info...")
        world_info = get_world_info()
        print("\nGenesis World Information:")
        print(f"Version: {world_info.get('version', 'unknown')}")
        print("\nAvailable modules:")
        for module_name in world_info.get("modules", {}).keys():
            print(f"  - {module_name}")
        print("\nAvailable top-level classes:")
        for class_name in world_info.get("classes", {}).keys():
            print(f"  - {class_name}")
        print("\nAvailable top-level functions:")
        for func_name in world_info.get("functions", {}).keys():
            print(f"  - {func_name}")
        
        print("\nExample simulations available:")
        for i, example in enumerate(world_info.get("examples", [])):
            print(f"  {i+1}. {example['name']}: {example['description']}")
            
    else:
        # Run a simple simulation
        print("Running a basic simulation...")
        
        code = """
# Create a world with an agent
world = gw.World()
agent = gw.Agent(position=(0, 0))
world.add_agent(agent)

# Set up parameters from the request
max_steps = parameters.get("max_steps", 5)

# Run simulation
for step in range(max_steps):
    # Move the agent randomly
    directions = ["north", "east", "south", "west"]
    agent.move(direction=directions[step % 4], distance=1)
    world.step()
    print(f"Step {step}: Agent at position {agent.position}")

# Return results
result = {
    "steps_completed": step + 1,
    "final_position": agent.position,
    "world_state": world.get_state()
}
"""
        
        parameters = {"max_steps": 10}
        result = run_simulation(code, parameters)
        
        print("\nSimulation result:")
        print_pretty_json(result["result"])
        
        print("\nSimulation logs:")
        for log in result["logs"]:
            print(f"  {log}") 