#!/bin/bash
# MBM Book - Build all kernel Docker images

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
KERNEL_DIR="$PROJECT_ROOT/kernels/docker"

echo "╔══════════════════════════════════════════════════╗"
echo "║    MBM Book - Building Kernel Docker Images      ║"
echo "╚══════════════════════════════════════════════════╝"

KERNELS=(
    "python"
    "node"
    "cpp"
    "java"
    "go"
    "rust"
    "r"
    "julia"
    "dotnet"
)

for kernel in "${KERNELS[@]}"; do
    echo ""
    echo "━━━ Building mbmbook-kernel-${kernel} ━━━"
    if [ -d "$KERNEL_DIR/$kernel" ]; then
        docker build -t "mbmbook-kernel-${kernel}" "$KERNEL_DIR/$kernel"
        echo "✅ mbmbook-kernel-${kernel} built successfully"
    else
        echo "⚠️  Skipping ${kernel}: no Dockerfile found"
    fi
done

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║    All kernel images built!                      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Built images:"
docker images | grep mbmbook-kernel
