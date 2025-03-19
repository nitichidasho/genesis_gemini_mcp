"""Models for the Genesis MCP server."""

from typing import Dict, List, Any

from pydantic import BaseModel


class SimulationResult(BaseModel):
    """Result from a Genesis World simulation."""
    result: Dict[str, Any]
    logs: List[str] 