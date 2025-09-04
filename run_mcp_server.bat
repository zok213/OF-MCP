@echo off
echo.
echo ====================================
echo  MCP Web Scraper Server Launcher
echo ====================================
echo.

cd /d "%~dp0"

if not exist "venv-mcp-scraper\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run deploy.py first to set up the environment.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo Warning: .env file not found. Creating from template...
    copy ".env.example" ".env"
    echo Please edit .env file to configure your settings.
    echo.
)

echo Starting MCP Web Scraper Server...
echo Press Ctrl+C to stop the server.
echo.

venv-mcp-scraper\Scripts\python.exe mcp-web-scraper\src\server.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server exited with error code %ERRORLEVEL%
    echo Check the logs in the logs\ directory for more information.
)

echo.
pause
