"""Data models for Genesis MCP."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class SimulationResult(BaseModel):
    """Result from a Genesis World simulation."""
    result: Dict[str, Any]
    logs: List[str] 