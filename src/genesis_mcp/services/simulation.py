"""Simulation service for Genesis World."""

import inspect
import logging
import sys
import traceback
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

import genesis as gs
from pydantic import BaseModel

from src.genesis_mcp.models import SimulationResult

logger = logging.getLogger(__name__)


class SimulationService:
    """Service for running Genesis World simulations."""
    
    def __init__(self):
        """Initialize the simulation service."""
        self.gs = gs
    
    def run_simulation(self, code: str, parameters: Dict[str, Any] = None) -> SimulationResult:
        """Run a Genesis World simulation from provided code.
        
        Args:
            code: Python code that uses Genesis World
            parameters: Optional parameters to pass to the simulation
            
        Returns:
            SimulationResult with simulation results and logs
        """
        logs = []
        result = {}
        
        # Create a string buffer to capture stdout for logs
        log_capture = StringIO()
        
        # Create a safe execution environment
        local_vars = {
            "gs": self.gs,
            "parameters": parameters or {},
            "result": result,
        }
        
        # Save original stdout and redirect to our capture
        original_stdout = sys.stdout
        sys.stdout = log_capture
        
        try:
            # Execute the simulation code
            exec(code, local_vars, local_vars)
            
            # Extract any results assigned to the result variable
            if "result" in local_vars:
                result = local_vars["result"]
                
            # Get the logs
            logs = log_capture.getvalue().splitlines()
            
            return SimulationResult(
                result=result,
                logs=logs
            )
            
        except Exception as e:
            logs.append(f"Error: {str(e)}")
            logs.append(traceback.format_exc())
            logger.exception("Error running simulation")
            
            return SimulationResult(
                result={"error": str(e)},
                logs=logs
            )
            
        finally:
            # Restore stdout
            sys.stdout = original_stdout
    
    def get_world_info(self) -> Dict[str, Any]:
        """Get information about the Genesis World API.
        
        Returns:
            Dictionary with information about available modules, classes, and functions
        """
        world_info = {
            "version": getattr(self.gs, "__version__", "unknown"),
            "modules": {},
            "examples": self._get_examples(),
        }
        
        # Collect module information
        for name, obj in inspect.getmembers(self.gs):
            if name.startswith("_"):
                continue
                
            if inspect.ismodule(obj):
                module_info = self._get_module_info(obj)
                if module_info:
                    world_info["modules"][name] = module_info
            elif inspect.isclass(obj):
                world_info["classes"] = world_info.get("classes", {})
                world_info["classes"][name] = self._get_class_info(obj)
            elif inspect.isfunction(obj):
                world_info["functions"] = world_info.get("functions", {})
                world_info["functions"][name] = self._get_function_info(obj)
                
        return world_info
    
    def _get_module_info(self, module) -> Dict[str, Any]:
        """Extract information about a module."""
        info = {
            "doc": inspect.getdoc(module),
            "classes": {},
            "functions": {}
        }
        
        for name, obj in inspect.getmembers(module):
            if name.startswith("_"):
                continue
                
            if inspect.isclass(obj):
                info["classes"][name] = self._get_class_info(obj)
            elif inspect.isfunction(obj):
                info["functions"][name] = self._get_function_info(obj)
                
        return info
    
    def _get_class_info(self, cls) -> Dict[str, Any]:
        """Extract information about a class."""
        return {
            "doc": inspect.getdoc(cls),
            "methods": {
                name: self._get_function_info(method)
                for name, method in inspect.getmembers(cls, inspect.isfunction)
                if not name.startswith("_")
            }
        }
    
    def _get_function_info(self, func) -> Dict[str, Any]:
        """Extract information about a function."""
        sig = inspect.signature(func)
        
        return {
            "doc": inspect.getdoc(func),
            "signature": str(sig),
            "parameters": {
                name: {
                    "default": str(param.default) if param.default is not inspect.Parameter.empty else None,
                    "annotation": str(param.annotation) if param.annotation is not inspect.Parameter.empty else None,
                }
                for name, param in sig.parameters.items()
            }
        }
    
    def _get_examples(self) -> List[Dict[str, str]]:
        """Get example simulations."""
        return [
            {
                "name": "Basic Simulation",
                "description": "A simple simulation of a world with moving agents",
                "code": """
# Create a simple world with agents
world = gs.World()
agent = gs.Agent(position=(0, 0))
world.add_agent(agent)

# Run the simulation for 10 steps
for step in range(10):
    agent.move(direction="north", distance=1)
    world.step()
    print(f"Step {step}: Agent at position {agent.position}")

# Return final world state
result = {
    "world_state": world.get_state(),
    "agent_positions": [a.position for a in world.agents]
}
"""
            },
            {
                "name": "Resource Collection Simulation",
                "description": "Agents collecting resources in a world",
                "code": """
# Create a world with resources
world = gs.World()

# Add resources to the world
for i in range(5):
    resource = gs.Resource(position=(i*5, i*5), type="food", quantity=10)
    world.add_resource(resource)

# Add agents with different strategies
collector_agent = gs.Agent(position=(0, 0), type="collector")
explorer_agent = gs.Agent(position=(10, 10), type="explorer")
world.add_agent(collector_agent)
world.add_agent(explorer_agent)

# Run simulation
for step in range(20):
    # Agents follow their strategies
    for agent in world.agents:
        if agent.type == "collector":
            # Collectors move toward nearest resource
            nearest = world.find_nearest_resource(agent.position)
            if nearest:
                direction = world.get_direction(agent.position, nearest.position)
                agent.move(direction=direction, distance=1)
                # Collect if at resource
                if agent.position == nearest.position:
                    agent.collect(nearest, quantity=1)
        elif agent.type == "explorer":
            # Explorers move randomly
            direction = ["north", "east", "south", "west"][step % 4]
            agent.move(direction=direction, distance=2)
    
    # Step the world forward
    world.step()
    print(f"Step {step}: Collector has {collector_agent.inventory}, Explorer has {explorer_agent.inventory}")

# Return results
result = {
    "steps": step + 1,
    "collector_inventory": collector_agent.inventory,
    "explorer_inventory": explorer_agent.inventory,
    "remaining_resources": [
        {"position": r.position, "quantity": r.quantity}
        for r in world.resources
    ]
}
"""
            }
        ]