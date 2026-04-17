"""
Resource Monitor - Real-time hardware resource monitoring.

Monitors CPU, RAM, GPU (NVIDIA), iGPU, and disk usage on each node.
Reports metrics for the cluster dashboard.
"""

import psutil
from dataclasses import dataclass, asdict


@dataclass
class ResourceSnapshot:
    cpu_percent: float = 0.0
    cpu_freq_mhz: float = 0.0
    cpu_cores_used: int = 0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    ram_percent: float = 0.0
    gpu_utilization: float | None = None
    gpu_memory_used_gb: float | None = None
    gpu_memory_total_gb: float | None = None
    gpu_temperature: float | None = None
    gpu_name: str | None = None
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    disk_percent: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0


class ResourceMonitor:
    """Monitors local hardware resources."""

    def __init__(self):
        self._gpu_available = False
        self._init_gpu()

    def _init_gpu(self):
        """Initialize GPU monitoring."""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            self._gpu_available = len(gpus) > 0
        except (ImportError, Exception):
            self._gpu_available = False

    def get_usage(self) -> dict:
        """Get current resource usage snapshot."""
        snapshot = ResourceSnapshot()

        # CPU
        snapshot.cpu_percent = psutil.cpu_percent(interval=0.1)
        freq = psutil.cpu_freq()
        if freq:
            snapshot.cpu_freq_mhz = freq.current
        snapshot.cpu_cores_used = sum(
            1 for p in (psutil.cpu_percent(percpu=True) or []) if p > 10.0
        )

        # RAM
        mem = psutil.virtual_memory()
        snapshot.ram_total_gb = round(mem.total / (1024 ** 3), 2)
        snapshot.ram_used_gb = round(mem.used / (1024 ** 3), 2)
        snapshot.ram_percent = mem.percent

        # GPU (NVIDIA)
        if self._gpu_available:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Primary GPU
                    snapshot.gpu_name = gpu.name
                    snapshot.gpu_utilization = gpu.load * 100
                    snapshot.gpu_memory_used_gb = round(gpu.memoryUsed / 1024, 2)
                    snapshot.gpu_memory_total_gb = round(gpu.memoryTotal / 1024, 2)
                    snapshot.gpu_temperature = gpu.temperature
            except Exception:
                pass

        # Disk
        disk = psutil.disk_usage("/")
        snapshot.disk_total_gb = round(disk.total / (1024 ** 3), 2)
        snapshot.disk_used_gb = round(disk.used / (1024 ** 3), 2)
        snapshot.disk_percent = round(disk.percent, 1)

        # Network
        net = psutil.net_io_counters()
        snapshot.network_sent_mb = round(net.bytes_sent / (1024 ** 2), 2)
        snapshot.network_recv_mb = round(net.bytes_recv / (1024 ** 2), 2)

        return asdict(snapshot)

    def get_processes(self, top_n: int = 10) -> list[dict]:
        """Get top processes by CPU/memory usage."""
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes.sort(key=lambda p: (p.get("cpu_percent") or 0), reverse=True)
        return processes[:top_n]


# Singleton
resource_monitor = ResourceMonitor()
