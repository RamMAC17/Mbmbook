<#
.SYNOPSIS
    Build all MBM Book kernel Docker images (Windows version)
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$KernelDir = Join-Path $ProjectRoot "kernels\docker"

Write-Host "Building MBM Book Kernel Docker Images..." -ForegroundColor Cyan

$kernels = @("python", "node", "cpp", "java", "go", "rust", "r", "julia", "dotnet")

foreach ($kernel in $kernels) {
    $dockerfilePath = Join-Path $KernelDir $kernel
    if (Test-Path $dockerfilePath) {
        Write-Host "`n--- Building mbmbook-kernel-$kernel ---" -ForegroundColor Yellow
        docker build -t "mbmbook-kernel-$kernel" $dockerfilePath
        Write-Host "  OK: mbmbook-kernel-$kernel" -ForegroundColor Green
    } else {
        Write-Host "  SKIP: $kernel (no Dockerfile)" -ForegroundColor Gray
    }
}

Write-Host "`nAll kernel images built!" -ForegroundColor Green
docker images | Select-String "mbmbook-kernel"
