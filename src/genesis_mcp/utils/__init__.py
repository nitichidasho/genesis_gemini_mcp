"""Utility functions for Genesis MCP server."""

import json
import logging
from typing import Any, Dict


def serialize_for_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable format.
    
    This handles special cases like complex objects that might come from Genesis World.
    """
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    else:
        return str(obj)


def safe_json_dumps(data: Dict) -> str:
    """Convert data to JSON string safely."""
    return json.dumps(data, default=serialize_for_json)


def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging for the MCP server."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ) 