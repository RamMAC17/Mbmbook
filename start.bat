@echo off
:: ╔══════════════════════════════════════════════════════════════╗
:: ║  MBM Book - One-Click Server Startup                       ║
:: ║  Run this as Administrator after PC restart                 ║
:: ║  Access: http://10.10.13.30  |  Docs: http://10.10.13.30/docs  ║
:: ╚══════════════════════════════════════════════════════════════╝

title MBM Book Server - 10.10.13.30

echo.
echo   Starting MBM Book Server...
echo   ════════════════════════════
echo.

:: Change to project directory
cd /d D:\MBMbook

:: Start Docker Desktop if not running (for isolated code execution)
docker info >nul 2>&1
if errorlevel 1 (
    echo   [1/3] Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo         Waiting for Docker daemon...
    :wait_docker
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 goto wait_docker
    echo         Docker is ready.
) else (
    echo   [1/3] Docker Desktop already running.
)

:: Verify the Python kernel image exists
docker image inspect mbmbook-kernel-python >nul 2>&1
if errorlevel 1 (
    echo   [2/3] Building Python kernel Docker image...
    docker build -t mbmbook-kernel-python -f docker\Dockerfile.python .
) else (
    echo   [2/3] Python kernel image ready.
)

:: Start the server
echo   [3/3] Starting Uvicorn server on port 80...
echo.
echo   ╔══════════════════════════════════════════════════════════╗
echo   ║  MBM Book is starting...                                ║
echo   ║  URL  : http://10.10.13.30                              ║
echo   ║  Docs : http://10.10.13.30/docs                         ║
echo   ║  Press Ctrl+C to stop the server                        ║
echo   ╚══════════════════════════════════════════════════════════╝
echo.

D:\MBMbook\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 80 --reload --reload-exclude data --reload-exclude frontend --reload-exclude .git
