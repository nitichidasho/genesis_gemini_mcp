"""Tests for the simulation service."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.genesis_mcp.models import SimulationResult
from src.genesis_mcp.services.simulation import SimulationService


@pytest.fixture
def service():
    """Create a simulation service with mocked Genesis World."""
    with patch("src.genesis_mcp.services.simulation.gw") as mock_gw:
        service = SimulationService()
        # Replace the gw attribute with our mock
        service.gw = mock_gw
        yield service


def test_run_simulation_success(service):
    """Test successfully running a simulation."""
    # Test code
    code = """
result = {"test": "value"}
print("Test log")
"""
    
    # Run the simulation
    result = service.run_simulation(code)
    
    # Check result
    assert isinstance(result, SimulationResult)
    assert result.result == {"test": "value"}
    assert "Test log" in result.logs


def test_run_simulation_with_parameters(service):
    """Test running a simulation with parameters."""
    # Test code that uses parameters
    code = """
result = {"param_value": parameters["test_param"]}
print(f"Parameter: {parameters['test_param']}")
"""
    
    # Run the simulation with parameters
    parameters = {"test_param": "test_value"}
    result = service.run_simulation(code, parameters)
    
    # Check result
    assert result.result == {"param_value": "test_value"}
    assert "Parameter: test_value" in result.logs


def test_run_simulation_error(service):
    """Test handling errors in simulation."""
    # Test code with error
    code = """
raise ValueError("Test error")
"""
    
    # Run the simulation
    result = service.run_simulation(code)
    
    # Check result
    assert "error" in result.result
    assert "Test error" in result.result["error"]
    assert any("Error: Test error" in log for log in result.logs)


def test_get_world_info(service):
    """Test getting world info."""
    # Set up mock for __version__
    service.gw.__version__ = "test-version"
    
    # Set up module, class, and function for inspection
    mock_module = MagicMock()
    mock_class = MagicMock()
    mock_function = MagicMock()
    
    # Configure inspect.getmembers to return our mocks
    with patch("src.genesis_mcp.services.simulation.inspect") as mock_inspect:
        mock_inspect.getmembers.side_effect = [
            [("test_module", mock_module)],  # First call returns modules
            [("test_class", mock_class)],    # Second call returns classes
            [("test_method", mock_function)]  # Third call returns functions
        ]
        mock_inspect.ismodule.return_value = True
        mock_inspect.isclass.return_value = True
        mock_inspect.isfunction.return_value = True
        mock_inspect.getdoc.return_value = "Test documentation"
        
        # Mock signature
        mock_param = MagicMock()
        mock_param.default = "default_value"
        mock_param.annotation = str
        mock_signature = MagicMock()
        mock_signature.parameters = {"param1": mock_param}
        mock_inspect.signature.return_value = mock_signature
        
        # Get world info
        world_info = service.get_world_info()
        
    # Check result
    assert world_info["version"] == "test-version"
    assert "modules" in world_info
    assert "examples" in world_info 