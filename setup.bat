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

REM Install PyTorch (required by genesis-world)
echo Installing PyTorch (required for genesis-world)...
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Create requirements.lock if it doesn't exist
if not exist requirements.lock (
    echo Creating requirements.lock from pyproject.toml...
    uv pip compile pyproject.toml -o requirements.lock
)

REM Install from the lock file
echo Installing dependencies from lock file...
uv pip install -r requirements.lock

REM Install the package in development mode
echo Installing the package in development mode...
uv pip install -e .

REM Uninstall pygel3d to avoid conflict with taichi
echo Uninstalling pygel3d to avoid conflict with taichi...
uv pip uninstall -y pygel3d

REM Install mcp without dependencies
echo Installing mcp package without dependencies...
uv pip install "mcp[cli]==1.4.1" --no-deps

REM Install mcp dependencies except pydantic
echo Installing mcp dependencies except pydantic...
uv pip install anyio httpx httpx-sse pydantic-settings sse-starlette "starlette<0.39.0,>=0.37.2" uvicorn

REM Ensure correct typing-extensions version
echo Installing correct version of typing-extensions...
uv pip install typing-extensions==4.12.0

REM Check if npm is installed
where npm >nul 2>&1
if %errorlevel% equ 0 (
    echo Installing MCP Inspector using Taobao npm registry for faster installation in China...
    npm install -g @modelcontextprotocol/inspector@0.6.0 --registry=https://registry.npmmirror.com
) else (
    echo WARNING: npm not found. MCP Inspector will not be installed.
    echo You can install it manually with: npm install -g @modelcontextprotocol/inspector@0.6.0 --registry=https://registry.npmmirror.com
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