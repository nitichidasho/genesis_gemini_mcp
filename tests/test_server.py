"""Tests for the Genesis MCP server."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.genesis_mcp.server import create_app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@patch("src.genesis_mcp.services.simulation.SimulationService")
def test_run_simulation(mock_service, client):
    """Test running a simulation through the MCP endpoint."""
    # Mock the simulation service
    mock_service.return_value.run_simulation.return_value = MagicMock(
        result={"test_result": True},
        logs=["Test log 1", "Test log 2"]
    )
    
    # Test data
    request_data = {
        "request_id": "test-123",
        "request_type": "run_simulation",
        "inputs": {
            "code": "print('hello world')",
            "parameters": {"test_param": "value"}
        }
    }
    
    # Call the endpoint
    response = client.post(
        "/mcp",
        json=request_data
    )
    
    # Check response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["request_id"] == "test-123"
    assert response_data["status"] == "success"
    assert response_data["outputs"]["result"] == {"test_result": True}
    assert response_data["outputs"]["logs"] == ["Test log 1", "Test log 2"]
    
    # Verify service was called correctly
    mock_service.return_value.run_simulation.assert_called_once_with(
        "print('hello world')", 
        {"test_param": "value"}
    )


@patch("src.genesis_mcp.services.simulation.SimulationService")
def test_get_world_info(mock_service, client):
    """Test getting world info through the MCP endpoint."""
    # Mock the simulation service
    mock_service.return_value.get_world_info.return_value = {
        "version": "test-version",
        "modules": {"test_module": {"functions": {}}},
        "examples": [{"name": "Test Example", "description": "Test description"}]
    }
    
    # Test data
    request_data = {
        "request_id": "info-123",
        "request_type": "get_world_info",
        "inputs": {}
    }
    
    # Call the endpoint
    response = client.post(
        "/mcp",
        json=request_data
    )
    
    # Check response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["request_id"] == "info-123"
    assert response_data["status"] == "success"
    assert response_data["outputs"]["world_info"]["version"] == "test-version"
    
    # Verify service was called
    mock_service.return_value.get_world_info.assert_called_once() 