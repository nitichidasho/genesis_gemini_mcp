"""Data models for Genesis MCP."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class SimulationResult(BaseModel):
    """Result from a Genesis World simulation."""
    result: Dict[str, Any] = Field(description="Simulation result data")
    logs: List[str] = Field(description="Execution logs and outputs")
    status: str = Field(default="completed", description="Execution status")
    error: Optional[str] = Field(default=None, description="Error message if any")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")


class SimulationRequest(BaseModel):
    """Request for running a simulation."""
    code: str = Field(description="Python code to execute")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameters")
    show_viewer: bool = Field(default=True, description="Whether to show Genesis viewer")
    timeout: Optional[int] = Field(default=30, description="Execution timeout in seconds")


class GenesisObject(BaseModel):
    """Represents a Genesis World object."""
    object_type: str = Field(description="Type of object (box, sphere, etc.)")
    position: List[float] = Field(default=[0, 0, 0], description="Object position [x, y, z]")
    properties: Dict[str, Any] = Field(default={}, description="Object properties")


class GenerationRequest(BaseModel):
    """Request for code generation."""
    description: str = Field(description="Natural language description")
    style: str = Field(default="simulation", description="Generation style")
    include_viewer: bool = Field(default=True, description="Include viewer in generated code") 