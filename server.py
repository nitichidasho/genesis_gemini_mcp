"""Genesis World MCP server using FastMCP with stdio transport."""

from mcp.server.fastmcp import FastMCP, Context
import logging
import sys

# Import the actual implementation
from src.genesis_mcp.services.simulation import SimulationService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Create simulation service
simulation_service = SimulationService()

# Create MCP server
logger.debug("Creating FastMCP server instance")
mcp = FastMCP("Genesis World")


@mcp.resource("world_info://{name}")
def get_world_info(name: str) -> str:
    """Get information about Genesis World features."""
    logger.debug(f"Resource request for world_info: {name}")
    
    # Get world info from the service
    world_info = simulation_service.get_world_info()
    
    if name == "overview":
        return """
        Genesis World is a simulation environment for creating and running complex simulations.
        It provides a variety of objects and tools for creating virtual worlds, agents, and resources.
        """
    elif name == "capabilities":
        return """
        - Create and manage simulation worlds
        - Add and control agents with various behaviors
        - Define and interact with resources
        - Run step-based simulations
        - Collect and analyze simulation results
        """
    elif name == "api":
        # Return the API details from the service
        return str(world_info)
    else:
        return f"No information available for '{name}'"


@mcp.tool()
def run_simulation(code: str, parameters: dict = None) -> dict:
    """Run a Genesis World simulation with the provided code and parameters.
    
    Args:
        code: Python code for the simulation
        parameters: Optional parameters for the simulation
        
    Returns:
        A dictionary with simulation results and logs
    """
    logger.debug(f"Simulation request with parameters: {parameters}")
    try:
        # Use the real simulation service implementation
        result = simulation_service.run_simulation(code, parameters)
        
        return {
            "success": True,
            "message": "Simulation executed successfully",
            "logs": result.logs,
            "results": result.result
        }
    except Exception as e:
        logger.exception("Error executing simulation")
        return {
            "success": False,
            "message": f"Error executing simulation: {str(e)}",
            "logs": [f"Error: {str(e)}"],
            "results": {}
        }


@mcp.prompt()
def basic_simulation(world_size: int = 10, agent_count: int = 2) -> str:
    """Create a basic simulation prompt.
    
    Args:
        world_size: Size of the simulation world
        agent_count: Number of agents to create
    """
    logger.debug(f"Prompt request for basic_simulation with world_size={world_size}, agent_count={agent_count}")
    
    # Get examples from the simulation service
    examples = simulation_service.get_world_info().get("examples", [])
    basic_example = next((e for e in examples if e.get("name") == "Basic Simulation"), None)
    
    # Use the example if found, otherwise use our default template
    if basic_example:
        # Customize the example with user parameters
        code = basic_example.get("code", "")
        # Replace any parameters in the code if needed
        # This is a simple example - you might need more sophisticated templating
        code = code.replace("world = gs.World()", f"world = gs.World(size=({world_size}, {world_size}))")
        return code
    
    # Fall back to our template
    return f"""
    # Basic Genesis World Simulation
    
    import genesis as gs
    
    # Create a world of size {world_size}x{world_size}
    world = gs.World(size=({world_size}, {world_size}))
    
    # Add {agent_count} agents to the world
    for i in range({agent_count}):
        agent = gs.Agent(position=(i, i))
        world.add_agent(agent)
    
    # Run the simulation for 10 steps
    for step in range(10):
        # Move each agent randomly
        for agent in world.agents:
            direction = ["north", "east", "south", "west"][step % 4]
            agent.move(direction=direction, distance=1)
        
        # Step the world forward
        world.step()
        print(f"Step {{step}}: Agents at {{[a.position for a in world.agents]}}")
    
    # Return the results
    result = {{
        "steps_completed": step + 1,
        "final_positions": [a.position for a in world.agents],
        "world_state": world.get_state()
    }}
    """

if __name__ == "__main__":
    logger.debug("Starting MCP server with stdio transport")
    
    try:
        # Use FastMCP's built-in transport support with stdio
        mcp.run(transport="stdio")
    except Exception as e:
        logger.exception("Error starting MCP server")
        raise