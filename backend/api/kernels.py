"""Kernel management API endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from backend.schemas import KernelLaunchRequest, KernelResponse
from backend.services.kernel_manager import kernel_manager

router = APIRouter()


@router.post("/launch", response_model=KernelResponse, status_code=201)
async def launch_kernel(req: KernelLaunchRequest):
    """Launch a new kernel for the specified language."""
    kernel = await kernel_manager.launch_kernel(
        language=req.language,
        notebook_id=str(req.notebook_id) if req.notebook_id else None,
        resource_profile=req.resource_profile,
    )
    return kernel


@router.get("/", response_model=list[KernelResponse])
async def list_kernels():
    """List all active kernels."""
    return kernel_manager.list_kernels()


@router.get("/{kernel_id}", response_model=KernelResponse)
async def get_kernel(kernel_id: str):
    """Get kernel details."""
    kernel = kernel_manager.get_kernel(kernel_id)
    if not kernel:
        raise HTTPException(status_code=404, detail="Kernel not found")
    return kernel


@router.post("/{kernel_id}/interrupt")
async def interrupt_kernel(kernel_id: str):
    """Interrupt a running kernel."""
    success = await kernel_manager.interrupt_kernel(kernel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kernel not found")
    return {"status": "interrupted"}


@router.post("/{kernel_id}/restart")
async def restart_kernel(kernel_id: str):
    """Restart a kernel."""
    kernel = await kernel_manager.restart_kernel(kernel_id)
    if not kernel:
        raise HTTPException(status_code=404, detail="Kernel not found")
    return kernel


@router.delete("/{kernel_id}", status_code=204)
async def shutdown_kernel(kernel_id: str):
    """Shutdown and remove a kernel."""
    success = await kernel_manager.shutdown_kernel(kernel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kernel not found")


@router.get("/languages/available")
async def list_available_languages():
    """List all supported languages with their kernel info."""
    return kernel_manager.get_available_languages()
