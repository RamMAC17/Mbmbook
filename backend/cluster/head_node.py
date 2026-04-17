"""
Head Node - Starts the Ray head node and the MBM Book API server.

Run on the primary lab PC that will coordinate the cluster.

Usage:
    python -m backend.cluster.head_node
    python -m backend.cluster.head_node --port 8000 --ray-port 6379
"""

import argparse
import asyncio
import socket


async def start_head_node(api_port: int = 8000, ray_port: int = 6379):
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║           MBM Book - Head Node                  ║")
    print(f"╠══════════════════════════════════════════════════╣")
    print(f"║  Hostname  : {hostname:<35} ║")
    print(f"║  IP Address: {ip:<35} ║")
    print(f"║  API Port  : {api_port:<35} ║")
    print(f"║  Ray Port  : {ray_port:<35} ║")
    print(f"╚══════════════════════════════════════════════════╝")

    # 1. Start Ray head node
    print("\n📡 Starting Ray head node...")
    try:
        import ray
        ray.init(
            num_cpus=20,
            num_gpus=1,
            dashboard_host="0.0.0.0",
            dashboard_port=8265,
            include_dashboard=True,
        )
        print(f"✅ Ray head started. Dashboard: http://{ip}:8265")
        print(f"   Resources: {ray.cluster_resources()}")
        print(f"   Workers connect with: --head-address {ip}:{ray_port}")
    except ImportError:
        print("⚠️ Ray not installed. Running in standalone mode.")
    except Exception as e:
        print(f"⚠️ Ray init error: {e}. Running in standalone mode.")

    # 2. Register self as head node
    from backend.services.cluster_manager import cluster_manager
    await cluster_manager.register_node(hostname, ip, is_head=True)
    print(f"✅ Registered as head node")

    # 3. Start API server
    print(f"\n🚀 Starting API server on http://{ip}:{api_port}")
    import uvicorn
    config = uvicorn.Config(
        "backend.app:app",
        host="0.0.0.0",
        port=api_port,
        reload=False,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


def main():
    parser = argparse.ArgumentParser(description="MBM Book Head Node")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    parser.add_argument("--ray-port", type=int, default=6379, help="Ray head port")
    args = parser.parse_args()

    asyncio.run(start_head_node(api_port=args.port, ray_port=args.ray_port))


if __name__ == "__main__":
    main()
