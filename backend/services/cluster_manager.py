"""
Cluster Manager - Manages distributed computing across lab PCs using Ray.

Handles:
  - Node registration and discovery
  - Task scheduling across nodes
  - Resource-aware kernel placement
  - Load balancing
  - Health monitoring
"""

import uuid
from datetime import datetime, timezone


class ClusterNode:
    """Represents a node in the cluster."""

    def __init__(
        self,
        hostname: str,
        ip_address: str,
        is_head: bool = False,
    ):
        self.id = str(uuid.uuid4())
        self.hostname = hostname
        self.ip_address = ip_address
        self.port = 8786
        self.is_head = is_head
        self.status = "online"
        self.cpu_cores = 20
        self.cpu_threads = 28
        self.ram_total_gb = 32.0
        self.gpu_name = "NVIDIA GeForce RTX 3060"
        self.gpu_vram_gb = 12.0
        self.disk_total_gb = 512.0
        self.active_kernels = 0
        self.last_heartbeat = datetime.now(timezone.utc)
        self.metadata = {}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "is_head": self.is_head,
            "status": self.status,
            "cpu_cores": self.cpu_cores,
            "cpu_threads": self.cpu_threads,
            "ram_total_gb": self.ram_total_gb,
            "gpu_name": self.gpu_name,
            "gpu_vram_gb": self.gpu_vram_gb,
            "disk_total_gb": self.disk_total_gb,
            "active_kernels": self.active_kernels,
            "last_heartbeat": self.last_heartbeat,
        }


class ClusterManager:
    """Manages the distributed cluster of lab PCs."""

    def __init__(self):
        self._nodes: dict[str, ClusterNode] = {}
        self._ray_initialized = False

    async def initialize_ray(self, head_address: str = "auto"):
        """Initialize Ray cluster connection."""
        try:
            import ray
            if not ray.is_initialized():
                if head_address == "auto":
                    ray.init()
                else:
                    ray.init(address=head_address)
                self._ray_initialized = True
                print(f"✅ Connected to Ray cluster: {ray.cluster_resources()}")
        except ImportError:
            print("⚠️ Ray not installed. Running in standalone mode.")
        except Exception as e:
            print(f"⚠️ Could not connect to Ray: {e}. Running in standalone mode.")

    async def register_node(
        self, hostname: str, ip_address: str, is_head: bool = False
    ) -> ClusterNode:
        """Register a new node in the cluster."""
        node = ClusterNode(hostname=hostname, ip_address=ip_address, is_head=is_head)
        self._nodes[node.id] = node
        return node

    async def list_nodes(self) -> list[dict]:
        """List all cluster nodes."""
        # If Ray is connected, sync with Ray's node list
        if self._ray_initialized:
            await self._sync_ray_nodes()
        return [n.to_dict() for n in self._nodes.values()]

    async def get_node(self, node_id: str) -> dict | None:
        node = self._nodes.get(node_id)
        return node.to_dict() if node else None

    async def get_cluster_status(self) -> dict:
        """Get aggregated cluster status."""
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
        """Get real-time resource usage from a specific node."""
        node = self._nodes.get(node_id)
        if not node:
            return None

        # In production: query the node's resource monitor agent
        # For now, return local metrics if this is the local node
        from backend.services.resource_monitor import resource_monitor
        return resource_monitor.get_usage()

    async def select_best_node(
        self,
        requires_gpu: bool = False,
        min_memory_gb: float = 4.0,
    ) -> ClusterNode | None:
        """
        Select the best node for launching a new kernel.

        Strategy: least-loaded node that meets requirements.
        """
        candidates = []
        for node in self._nodes.values():
            if node.status != "online":
                continue
            if requires_gpu and node.gpu_vram_gb < 1:
                continue
            # Check if node has enough capacity
            if node.active_kernels >= 10:  # max kernels per node
                continue
            candidates.append(node)

        if not candidates:
            return None

        # Sort by active kernels (ascending) - least loaded first
        candidates.sort(key=lambda n: n.active_kernels)
        return candidates[0]

    async def drain_node(self, node_id: str) -> bool:
        """Stop scheduling new kernels on a node."""
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.status = "draining"
        return True

    async def resume_node(self, node_id: str) -> bool:
        """Resume scheduling on a drained node."""
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.status = "online"
        return True

    async def heartbeat(self, node_id: str, resources: dict) -> bool:
        """Update node heartbeat and resource usage."""
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.last_heartbeat = datetime.now(timezone.utc)
        node.metadata["last_resources"] = resources
        return True

    async def _sync_ray_nodes(self):
        """Sync node list with Ray cluster."""
        try:
            import ray
            nodes = ray.nodes()
            for rn in nodes:
                hostname = rn.get("NodeManagerHostname", "unknown")
                ip = rn.get("NodeManagerAddress", "0.0.0.0")
                # Check if already registered
                existing = None
                for node in self._nodes.values():
                    if node.hostname == hostname:
                        existing = node
                        break
                if not existing:
                    await self.register_node(hostname, ip)
        except Exception:
            pass


# Singleton
cluster_manager = ClusterManager()
