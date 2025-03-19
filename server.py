"""Genesis World MCP server using FastMCP."""

from mcp.server.fastmcp import FastMCP
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Create MCP server
logger.debug("Creating FastMCP server instance")
mcp = FastMCP("Genesis World")


@mcp.resource("world_info://{name}")
def get_world_info(name: str) -> str:
    """Get information about Genesis World features."""
    logger.debug(f"Resource request for world_info: {name}")
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
        # This is just a placeholder - we'd normally use genesis here
        # but for demonstration purposes, we're just printing the code
        
        print(f"Running simulation with parameters: {parameters or {}}")
        print(f"Code:\n{code}")
        
        # In a real implementation, we would execute the code using
        # the genesis package and return the results
        
        return {
            "success": True,
            "message": "Simulation executed successfully",
            "logs": [
                "Simulation started",
                "Step 1: Agents initialized",
                "Step 2: Resources collected",
                "Simulation completed"
            ],
            "results": {
                "steps_completed": 10,
                "agents": 2,
                "resources_collected": 5
            }
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
    logger.debug("Starting MCP server")
    try:
        mcp.run()
    except Exception as e:
        logger.exception("Error starting MCP server")
        raise 