"""MCP server implementation for Genesis World."""

import logging
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.genesis_mcp.services.simulation import SimulationService

logger = logging.getLogger(__name__)


class SimulationResult(BaseModel):
    """Result from a Genesis World simulation."""
    result: Dict
    logs: List[str]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application for MCP."""
    app = FastAPI(title="Genesis World MCP Server")
    simulation_service = SimulationService()

    @app.post("/mcp")
    async def handle_mcp_request(request: dict) -> dict:
        """Handle MCP requests by executing Genesis World simulations."""
        try:
            request_id = request.get("request_id", "unknown")
            request_type = request.get("request_type", "")
            inputs = request.get("inputs", {})
            
            logger.info(f"Received MCP request: {request_type}")
            
            if request_type == "run_simulation":
                # Extract simulation code and parameters from the request
                if not inputs or "code" not in inputs:
                    raise HTTPException(status_code=400, detail="Missing simulation code")
                
                code = inputs["code"]
                params = inputs.get("parameters", {})
                
                # Run the simulation
                result = simulation_service.run_simulation(code, params)
                
                # Return the response
                return {
                    "request_id": request_id,
                    "outputs": {"result": result.result, "logs": result.logs},
                    "status": "success"
                }
            
            elif request_type == "get_world_info":
                # Return information about available world features
                world_info = simulation_service.get_world_info()
                return {
                    "request_id": request_id,
                    "outputs": {"world_info": world_info},
                    "status": "success"
                }
            
            else:
                return {
                    "request_id": request_id,
                    "status": "error",
                    "error_message": f"Unsupported request type: {request_type}"
                }
                
        except Exception as e:
            logger.exception("Error processing MCP request")
            return {
                "request_id": request.get("request_id", "unknown"),
                "status": "error",
                "error_message": str(e)
            }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app 