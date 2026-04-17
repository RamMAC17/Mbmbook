"""Cluster management API endpoints."""

from fastapi import APIRouter, HTTPException
from backend.schemas import ClusterNodeResponse, ClusterStatus, ResourceUsage
from backend.services.cluster_manager import cluster_manager

router = APIRouter()


@router.get("/status", response_model=ClusterStatus)
async def get_cluster_status():
    """Get overall cluster status and resource summary."""
    return await cluster_manager.get_cluster_status()


@router.get("/nodes", response_model=list[ClusterNodeResponse])
async def list_nodes():
    """List all cluster nodes."""
    return await cluster_manager.list_nodes()


@router.get("/nodes/{node_id}", response_model=ClusterNodeResponse)
async def get_node(node_id: str):
    """Get specific node details."""
    node = await cluster_manager.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/nodes/{node_id}/resources", response_model=ResourceUsage)
async def get_node_resources(node_id: str):
    """Get real-time resource usage for a node."""
    usage = await cluster_manager.get_node_resources(node_id)
    if not usage:
        raise HTTPException(status_code=404, detail="Node not found")
    return usage


@router.post("/nodes/{node_id}/drain")
async def drain_node(node_id: str):
    """Drain a node (stop scheduling new kernels, wait for existing to finish)."""
    success = await cluster_manager.drain_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"status": "draining"}


@router.post("/nodes/{node_id}/resume")
async def resume_node(node_id: str):
    """Resume a drained node."""
    success = await cluster_manager.resume_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"status": "online"}
