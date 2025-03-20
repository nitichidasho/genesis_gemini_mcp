@echo off
echo Setting up Genesis MCP environment using lock file...

REM Check if uv is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: uv package manager is not installed.
    echo Install it with: pip install uv
    exit /b 1
)

REM Remove uv.lock if it exists to avoid conflicts with mcp dev
if exist uv.lock (
    echo Removing uv.lock to avoid conflicts with mcp dev...
    del uv.lock
)

REM Force recreate the virtual environment to ensure it's clean
echo Creating fresh virtual environment with uv...
if exist .venv rmdir /s /q .venv
uv venv .venv

REM Ensure proper activation by using the absolute path
echo Activating virtual environment...
call "%CD%\.venv\Scripts\activate.bat"

REM Verify Python interpreter is working
echo Verifying Python interpreter...
where python

REM Create requirements.lock if it doesn't exist
if not exist requirements.lock (
    echo Creating requirements.lock from pyproject.toml...
    uv pip compile pyproject.toml -o requirements.lock
)

REM Install from the lock file
echo Installing dependencies from lock file...
uv pip install -r requirements.lock

REM Install genesis without dependencies
echo Installing genesis without dependencies...
uv pip install genesis==0.2.1 --no-deps

REM Install the package in development mode
echo Installing the package in development mode...
uv pip install -e .

REM Check if npm is installed
where npm >nul 2>&1
if %errorlevel% equ 0 (
    echo Installing MCP Inspector...
    npm install -g @modelcontextprotocol/inspector@0.6.0
) else (
    echo WARNING: npm not found. MCP Inspector will not be installed.
    echo You can install it manually with: npm install -g @modelcontextprotocol/inspector@0.6.0
)

echo.
echo Setup completed successfully!
echo.
echo To activate the virtual environment:
echo call "%CD%\.venv\Scripts\activate.bat"
echo.
echo To start the server:
echo mcp run server.py
echo.
echo Happy hacking! 