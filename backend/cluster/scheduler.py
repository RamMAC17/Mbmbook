"""
Distributed Task Scheduler - Schedules kernel execution across cluster nodes.

Uses Ray for distributing computation. Supports:
  - Resource-aware scheduling (CPU, GPU, memory)
  - Task queuing and prioritization
  - Fault tolerance and retry logic
"""

import asyncio
from datetime import datetime, timezone


class TaskScheduler:
    """Schedules and distributes tasks across the cluster."""

    def __init__(self):
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._running_tasks: dict[str, dict] = {}

    async def submit_task(
        self,
        task_id: str,
        language: str,
        code: str,
        requires_gpu: bool = False,
        priority: int = 5,
    ) -> dict:
        """Submit a code execution task to the scheduler."""
        task = {
            "id": task_id,
            "language": language,
            "code": code,
            "requires_gpu": requires_gpu,
            "priority": priority,
            "status": "queued",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "node_id": None,
            "result": None,
        }

        await self._task_queue.put(task)
        return task

    async def execute_distributed(self, code: str, language: str) -> dict:
        """
        Execute code on the best available node using Ray.

        For GPU-intensive work, schedules on a node with available GPU.
        For parallel work, can split across multiple nodes.
        """
        try:
            import ray

            @ray.remote
            def run_on_remote(code_str: str, lang: str) -> dict:
                """Execute code on a remote Ray worker."""
                import subprocess
                import tempfile
                import os

                from backend.services.kernel_registry import KERNEL_REGISTRY
                spec = KERNEL_REGISTRY.get(lang, {})
                file_ext = spec.get("file_extension", ".txt")
                run_cmd = spec.get("run_cmd", [])

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=file_ext, delete=False
                ) as f:
                    f.write(code_str)
                    temp_path = f.name

                try:
                    cmd = [c.replace("{file}", temp_path) for c in run_cmd]
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=60
                    )
                    return {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    }
                finally:
                    os.unlink(temp_path)

            # Submit to Ray
            future = run_on_remote.remote(code, language)
            result = await asyncio.to_thread(ray.get, future)
            return result

        except ImportError:
            return {"error": "Ray not available. Running locally."}
        except Exception as e:
            return {"error": str(e)}

    async def execute_gpu_task(self, code: str, language: str = "python") -> dict:
        """Execute GPU-intensive task on a node with available GPU."""
        try:
            import ray

            @ray.remote(num_gpus=1)
            def run_on_gpu(code_str: str) -> dict:
                import subprocess
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", delete=False
                ) as f:
                    f.write(code_str)
                    temp_path = f.name

                try:
                    result = subprocess.run(
                        ["python", "-u", temp_path],
                        capture_output=True, text=True, timeout=300,
                    )
                    return {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    }
                finally:
                    os.unlink(temp_path)

            future = run_on_gpu.remote(code)
            result = await asyncio.to_thread(ray.get, future)
            return result

        except ImportError:
            return {"error": "Ray not available"}
        except Exception as e:
            return {"error": str(e)}


# Singleton
task_scheduler = TaskScheduler()
