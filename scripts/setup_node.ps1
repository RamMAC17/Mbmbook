<#
.SYNOPSIS
    MBM Book - Lab PC Setup Script (Windows 11 Pro)
    Run this on EACH lab PC to prepare it as a cluster node.

.DESCRIPTION
    Installs and configures all prerequisites:
    - WSL2 + Ubuntu
    - Docker Desktop with NVIDIA GPU support
    - Python 3.11+
    - Node.js 20
    - Ray (distributed computing)
    - NVIDIA Container Toolkit (for GPU kernels)
    - Various language runtimes

.NOTES
    Run as Administrator!
    Hardware: Intel i7-14700 | 32GB DDR5 | RTX 3060 12GB | 512GB SSD | Win11 Pro
#>

param(
    [switch]$SkipWSL,
    [switch]$SkipDocker,
    [switch]$HeadNode,
    [string]$HeadAddress = ""
)

$ErrorActionPreference = "Continue"

Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        MBM Book - Node Setup Script             ║" -ForegroundColor Cyan
Write-Host "║        Lab PC Configuration                     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ──── Check Admin ────
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Run this script as Administrator!" -ForegroundColor Red
    exit 1
}

# ──── System Info ────
Write-Host "System Info:" -ForegroundColor Yellow
Write-Host "  Hostname : $env:COMPUTERNAME"
Write-Host "  OS       : $(Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)"
Write-Host "  CPU      : $((Get-CimInstance Win32_Processor).Name)"
Write-Host "  RAM      : $([math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)) GB"
Write-Host ""

# ──── 1. Enable WSL2 ────
if (-not $SkipWSL) {
    Write-Host "[1/7] Enabling WSL2..." -ForegroundColor Green
    wsl --install --no-distribution 2>$null
    wsl --set-default-version 2
    Write-Host "  WSL2 enabled." -ForegroundColor Gray
}

# ──── 2. Install Chocolatey (package manager) ────
Write-Host "[2/7] Installing Chocolatey..." -ForegroundColor Green
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-Host "  Chocolatey installed." -ForegroundColor Gray
} else {
    Write-Host "  Chocolatey already installed." -ForegroundColor Gray
}

# ──── 3. Install Core Tools ────
Write-Host "[3/7] Installing core tools..." -ForegroundColor Green

# Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    choco install python311 -y --no-progress
}
Write-Host "  Python: $(python --version 2>&1)" -ForegroundColor Gray

# Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    choco install nodejs-lts -y --no-progress
}
Write-Host "  Node.js: $(node --version 2>&1)" -ForegroundColor Gray

# Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    choco install git -y --no-progress
}

# ──── 4. Install Docker Desktop ────
if (-not $SkipDocker) {
    Write-Host "[4/7] Installing Docker Desktop..." -ForegroundColor Green
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        choco install docker-desktop -y --no-progress
        Write-Host "  Docker Desktop installed. Restart may be required." -ForegroundColor Yellow
    } else {
        Write-Host "  Docker: $(docker --version 2>&1)" -ForegroundColor Gray
    }
}

# ──── 5. Install NVIDIA Container Toolkit ────
Write-Host "[5/7] Checking NVIDIA GPU..." -ForegroundColor Green
$nvidiaSmi = nvidia-smi 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  NVIDIA GPU detected:" -ForegroundColor Gray
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>$null | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    Write-Host "  NVIDIA Container Toolkit will be available via Docker Desktop WSL2 backend." -ForegroundColor Gray
} else {
    Write-Host "  No NVIDIA GPU detected or drivers not installed." -ForegroundColor Yellow
}

# ──── 6. Install Python dependencies ────
Write-Host "[6/7] Installing Python dependencies..." -ForegroundColor Green
python -m pip install --upgrade pip
python -m pip install `
    fastapi uvicorn[standard] websockets `
    sqlalchemy asyncpg alembic `
    redis pydantic pydantic-settings `
    python-jose[cryptography] passlib[bcrypt] python-multipart `
    pyzmq jupyter-client jupyter-core `
    "ray[default]" docker psutil GPUtil `
    httpx aiofiles orjson

Write-Host "  Python dependencies installed." -ForegroundColor Gray

# ──── 7. Install additional language runtimes ────
Write-Host "[7/7] Installing language runtimes..." -ForegroundColor Green

# Go
if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    choco install golang -y --no-progress 2>$null
}

# Rust
if (-not (Get-Command rustc -ErrorAction SilentlyContinue)) {
    choco install rust -y --no-progress 2>$null
}

# Ruby
if (-not (Get-Command ruby -ErrorAction SilentlyContinue)) {
    choco install ruby -y --no-progress 2>$null
}

# Java
if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    choco install temurin21jdk -y --no-progress 2>$null
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          Setup Complete!                        ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║                                                  ║" -ForegroundColor Green
if ($HeadNode) {
    Write-Host "║  This node is configured as HEAD NODE.          ║" -ForegroundColor Green
    Write-Host "║  Start with:                                     ║" -ForegroundColor Green
    Write-Host "║    python -m backend.cluster.head_node           ║" -ForegroundColor Green
} else {
    Write-Host "║  This node is configured as WORKER NODE.         ║" -ForegroundColor Green
    Write-Host "║  Start with:                                     ║" -ForegroundColor Green
    Write-Host "║    python -m backend.cluster.worker_node \       ║" -ForegroundColor Green
    Write-Host "║      --head-address <HEAD_IP>:6379               ║" -ForegroundColor Green
}
Write-Host "║                                                  ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
