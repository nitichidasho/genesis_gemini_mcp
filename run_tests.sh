#!/bin/bash
# Run tests with coverage

set -e

# Run pytest with coverage
python -m pytest tests/ --cov=src/genesis_mcp --cov-report=term-missing 