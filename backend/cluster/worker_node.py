"""
Worker Node - Joins the Ray cluster and registers with the head node.

Run on each lab PC that should contribute resources.

Usage:
    python -m backend.cluster.worker_node --head-address 192.168.1.100:6379
    python -m backend.cluster.worker_node --head-address 192.168.1.100:6379 --api-url http://192.168.1.100:8000
"""

import argparse
import asyncio
import socket
import time


async def start_worker_node(head_address: str, api_url: str):
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║         MBM Book - Worker Node                  ║")
    print(f"╠══════════════════════════════════════════════════╣")
    print(f"║  Hostname   : {hostname:<34} ║")
    print(f"║  IP Address : {ip:<34} ║")
    print(f"║  Head Node  : {head_address:<34} ║")
    print(f"║  API URL    : {api_url:<34} ║")
    print(f"╚══════════════════════════════════════════════════╝")

    # 1. Connect to Ray cluster
    print(f"\n📡 Connecting to Ray cluster at {head_address}...")
    try:
        import ray
        ray.init(address=f"ray://{head_address}")
        print(f"✅ Connected to Ray cluster")
        print(f"   Cluster resources: {ray.cluster_resources()}")
    except ImportError:
        print("⚠️ Ray not installed. Install with: pip install 'ray[default]'")
    except Exception as e:
        print(f"⚠️ Could not connect to Ray: {e}")

    # 2. Register with head node API
    print(f"\n📝 Registering with head node at {api_url}...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{api_url}/api/v1/cluster/nodes",
                json={"hostname": hostname, "ip_address": ip},
            )
            if resp.status_code in (200, 201):
                print(f"✅ Registered with head node")
            else:
                print(f"⚠️ Registration response: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Could not register with head: {e}")

    # 3. Start resource monitor + heartbeat loop
    print(f"\n💓 Starting heartbeat loop...")
    from backend.services.resource_monitor import resource_monitor

    while True:
        try:
            usage = resource_monitor.get_usage()
            print(f"  CPU: {usage['cpu_percent']:.1f}% | "
                  f"RAM: {usage['ram_used_gb']:.1f}/{usage['ram_total_gb']:.1f} GB | "
                  f"GPU: {usage.get('gpu_utilization', 'N/A')}%")

            # Send heartbeat to head node
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{api_url}/api/v1/cluster/heartbeat",
                        json={"hostname": hostname, "resources": usage},
                        timeout=5.0,
                    )
            except Exception:
                pass  # Head node may be temporarily unavailable

            await asyncio.sleep(10)  # Heartbeat every 10 seconds

        except KeyboardInterrupt:
            print("\n🛑 Worker node shutting down...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(10)


def main():
    parser = argparse.ArgumentParser(description="MBM Book Worker Node")
    parser.add_argument(
        "--head-address", required=True,
        help="Ray head node address (e.g., 192.168.1.100:6379)"
    )
    parser.add_argument(
        "--api-url", default="http://localhost:8000",
        help="Head node API URL"
    )
    args = parser.parse_args()

    asyncio.run(start_worker_node(
        head_address=args.head_address,
        api_url=args.api_url,
    ))


if __name__ == "__main__":
    main()
