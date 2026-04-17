"""Core configuration for MBM Book."""

import ipaddress
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "MBM Book"
    app_version: str = "0.1.0"
    debug: bool = True
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    api_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Network Access Control
    # Supports multiple comma-separated subnets:
    # College LAN + APIPA (169.254.x.x) + common static IP ranges
    # This allows direct PC-to-PC ethernet connections without a router
    allowed_subnet: str = "10.10.12.0/23,169.254.0.0/16,192.168.0.0/16,172.16.0.0/12,10.0.0.0/8"
    host_ip: str = "10.10.13.242"

    # Database (SQLite for single-PC, PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///data/mbmbook.db"
    redis_url: str = "redis://localhost:6379/0"

    # Cluster
    ray_head_address: str = "auto"
    ray_dashboard_port: int = 8265
    cluster_name: str = "mbmbook-cluster"

    # Docker
    docker_network: str = "mbmbook-net"
    kernel_image_prefix: str = "mbmbook-kernel"
    kernel_timeout: int = 3600  # seconds
    max_kernels_per_node: int = 10

    # Storage
    notebooks_dir: Path = Path("data/notebooks")
    uploads_dir: Path = Path("data/uploads")

    # Resource Limits (per kernel)
    default_cpu_limit: float = 2.0  # cores
    default_memory_limit: str = "4g"
    default_gpu_limit: int = 0  # 0 = no GPU

    # WebSocket
    ws_heartbeat_interval: int = 30

    model_config = {"env_prefix": "MBM_", "env_file": ".env"}

    def is_ip_allowed(self, client_ip: str) -> bool:
        """Check if a client IP is within any of the allowed subnets.
        Supports direct PC-to-PC connections via APIPA or static IPs."""
        try:
            addr = ipaddress.ip_address(client_ip)
            # Always allow localhost
            if addr.is_loopback or client_ip in ("127.0.0.1", "::1"):
                return True
            # Allow the host itself
            if client_ip == self.host_ip:
                return True
            # Check against all allowed subnets (comma-separated)
            for subnet_str in self.allowed_subnet.split(","):
                subnet_str = subnet_str.strip()
                if not subnet_str:
                    continue
                network = ipaddress.ip_network(subnet_str, strict=False)
                if addr in network:
                    return True
            return False
        except ValueError:
            return False


settings = Settings()

# Ensure directories exist
settings.notebooks_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
