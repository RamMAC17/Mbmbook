"""
Cluster Manager - Manages this PC as the notebook execution server.

Shows real hardware info only (no fake nodes).
"""

import uuid
import subprocess
import psutil
from datetime import datetime, timezone


def _get_gpu_info():
    """Get GPU info via nvidia-smi (works on all Python versions)."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            name = parts[0].strip()
            vram_mb = float(parts[1].strip())
            return name, round(vram_mb / 1024, 1)
    except Exception:
        pass
    return None, 0.0


def _get_real_hw():
    """Get real hardware info from this PC."""
    cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count() or 1
    ram_total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    disk_total_gb = round(psutil.disk_usage("/").total / (1024 ** 3), 1)

    gpu_name, gpu_vram_gb = _get_gpu_info()

    return cpu_cores, ram_total_gb, gpu_name, gpu_vram_gb, disk_total_gb


class ClusterNode:
    """Represents this server node."""

    def __init__(
        self,
        hostname: str,
        ip_address: str,
        is_head: bool = True,
    ):
        self.id = str(uuid.uuid4())
        self.hostname = hostname
        self.ip_address = ip_address
        self.port = 80
        self.is_head = is_head
        self.status = "online"

        # Real hardware data
        cores, ram, gpu, vram, disk = _get_real_hw()
        self.cpu_cores = cores
        self.ram_total_gb = ram
        self.gpu_name = gpu or "None"
        self.gpu_vram_gb = vram
        self.disk_total_gb = disk

        self.active_kernels = 0
        self.last_heartbeat = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "is_head": self.is_head,
            "status": self.status,
            "cpu_cores": self.cpu_cores,
            "cpu_threads": psutil.cpu_count() or self.cpu_cores,
            "ram_total_gb": self.ram_total_gb,
            "gpu_name": self.gpu_name,
            "gpu_vram_gb": self.gpu_vram_gb,
            "disk_total_gb": self.disk_total_gb,
            "active_kernels": self.active_kernels,
            "last_heartbeat": self.last_heartbeat,
        }


class ClusterManager:
    """Manages this single server node (real data only)."""

    def __init__(self):
        self._nodes: dict[str, ClusterNode] = {}

    async def register_node(
        self, hostname: str, ip_address: str, is_head: bool = True
    ) -> ClusterNode:
        """Register this PC as the server node."""
        node = ClusterNode(hostname=hostname, ip_address=ip_address, is_head=is_head)
        self._nodes[node.id] = node
        return node

    async def list_nodes(self) -> list[dict]:
        return [n.to_dict() for n in self._nodes.values()]

    async def get_node(self, node_id: str) -> dict | None:
        node = self._nodes.get(node_id)
        return node.to_dict() if node else None

    async def get_cluster_status(self) -> dict:
        nodes = list(self._nodes.values())
        online = [n for n in nodes if n.status == "online"]
        return {
            "total_nodes": len(nodes),
            "online_nodes": len(online),
            "total_cpu_cores": sum(n.cpu_cores for n in online),
            "total_ram_gb": sum(n.ram_total_gb for n in online),
            "total_gpu_vram_gb": sum(n.gpu_vram_gb for n in online),
            "active_kernels": sum(n.active_kernels for n in online),
            "nodes": [n.to_dict() for n in nodes],
        }

    async def get_node_resources(self, node_id: str) -> dict | None:
        node = self._nodes.get(node_id)
        if not node:
            return None
        from backend.services.resource_monitor import resource_monitor
        return resource_monitor.get_usage()

    async def drain_node(self, node_id: str) -> bool:
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.status = "draining"
        return True

    async def resume_node(self, node_id: str) -> bool:
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.status = "online"
        return True


# Singleton
cluster_manager = ClusterManager()
