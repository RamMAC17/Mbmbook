@echo off
:: ╔══════════════════════════════════════════════════════════════╗
:: ║  MBM Book - One Click Setup & Launch                        ║
:: ║  Requirements: Docker Desktop installed                     ║
:: ║  Just clone the repo and double-click this file!            ║
:: ╚══════════════════════════════════════════════════════════════╝

title MBM Book - One Click Setup
color 0A

echo.
echo   ╔══════════════════════════════════════════════════════════╗
echo   ║         MBM Book - Notebook Platform Setup              ║
echo   ║   Like Google Colab / Jupyter - runs on your LAN       ║
echo   ╚══════════════════════════════════════════════════════════╝
echo.

:: Navigate to this script's directory (portable - works from any PC)
cd /d "%~dp0"

:: ─── Detect docker compose command (v2 plugin vs v1 standalone) ───
set "DC=docker compose"
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose version >nul 2>&1
    if errorlevel 1 (
        echo   ERROR: Neither 'docker compose' nor 'docker-compose' found.
        echo   Please install Docker Desktop from https://docker.com/products/docker-desktop
        pause
        exit /b 1
    )
    set "DC=docker-compose"
)

:: ─── 1. Check / Start Docker Desktop ───
echo   [1/4] Checking Docker Desktop...
docker info >nul 2>&1
if errorlevel 1 (
    echo         Docker not running. Starting Docker Desktop...
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) else (
        echo.
        echo   ERROR: Docker Desktop not found!
        echo   Please install from https://docker.com/products/docker-desktop
        echo.
        pause
        exit /b 1
    )
    :wait_docker
    echo         Waiting for Docker daemon to start...
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 goto wait_docker
    echo         Docker Desktop started successfully.
) else (
    echo         Docker Desktop is running.
)

:: ─── 2. Create data directories ───
echo   [2/4] Setting up data directories...
if not exist "data\notebooks" mkdir "data\notebooks"
if not exist "data\uploads" mkdir "data\uploads"
echo         Data directories ready.

:: ─── 3. Build Python kernel image (full ML stack) ───
echo   [3/4] Building Python kernel image...
echo         (First time takes ~15-30 min: TensorFlow, PyTorch, OpenCV, 80+ libs)
echo         (Subsequent runs use cache and are much faster)
docker build -t mbmbook-kernel-python -f kernels\docker\python\Dockerfile kernels\docker\python\
if errorlevel 1 (
    echo.
    echo   ERROR: Failed to build Python kernel image.
    echo   Check your internet connection and try again.
    pause
    exit /b 1
)
echo         Python kernel image built successfully.

:: ─── 4. Build and start MBM Book via Docker Compose ───
echo   [4/4] Building and starting MBM Book...
%DC% down >nul 2>&1
%DC% up --build -d
if errorlevel 1 (
    echo.
    echo   ERROR: Failed to start MBM Book.
    echo   Run '%DC% logs' for details.
    pause
    exit /b 1
)

:: ─── Auto-detect LAN IP for display ───
set "LAN_IP=localhost"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4" ^| findstr "10."') do (
    for /f "tokens=*" %%b in ("%%a") do set "LAN_IP=%%b"
)

echo.
echo   ╔══════════════════════════════════════════════════════════╗
echo   ║         MBM Book is RUNNING!                            ║
echo   ║                                                          ║
echo   ║  Local : http://localhost:9999                           ║
echo   ║  LAN   : http://%LAN_IP%:9999                       ║
echo   ║  Docs  : http://localhost:9999/docs                      ║
echo   ║                                                          ║
echo   ║  Python kernel includes 80+ libraries:                   ║
echo   ║  TensorFlow, PyTorch, OpenCV, Pillow, scikit-learn,     ║
echo   ║  pandas, numpy, matplotlib, seaborn, plotly, nltk,      ║
echo   ║  spacy, transformers, xgboost, and more!                ║
echo   ╚══════════════════════════════════════════════════════════╝
echo.

:: Open browser after short delay
timeout /t 3 /nobreak >nul
start http://localhost:9999

echo   Press any key to STOP the server and shut down...
pause >nul

echo.
echo   Shutting down MBM Book...
%DC% down
echo   Done. Goodbye!
timeout /t 2 >nul
