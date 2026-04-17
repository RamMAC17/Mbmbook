"""
Kernel Manager - Multi-language kernel lifecycle management.

Supports Docker-containerized execution (enterprise/Colab-like) with automatic
fallback to subprocess when Docker is not available.
"""

import asyncio
import os
import sys
import shutil
import uuid
import tempfile
from datetime import datetime, timezone
from typing import AsyncGenerator
from backend.services.kernel_registry import KERNEL_REGISTRY


def _docker_available() -> bool:
    """Check if Docker CLI exists AND daemon is responding (with timeout)."""
    if shutil.which("docker") is None:
        return False
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


class KernelInstance:
    """Represents a running kernel instance."""

    def __init__(self, kernel_id: str, language: str, node_id: str | None = None):
        self.id = kernel_id
        self.language = language
        self.node_id = node_id
        self.container_id: str | None = None
        self.status: str = "starting"
        self.started_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.resource_usage: dict = {}
        self.execution_count = 0
        self._process: asyncio.subprocess.Process | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "language": self.language,
            "status": self.status,
            "node_id": self.node_id,
            "container_id": self.container_id,
            "resource_usage": self.resource_usage,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


class KernelManager:
    """Manages kernel lifecycles with Docker and subprocess backends."""

    def __init__(self):
        self._kernels: dict[str, KernelInstance] = {}
        self._language_kernels: dict[str, list[str]] = {}
        self._docker_ok: bool | None = None  # lazy-checked

    @property
    def docker_available(self) -> bool:
        if self._docker_ok is None:
            self._docker_ok = _docker_available()
        return self._docker_ok

    async def _docker_image_exists(self, image: str) -> bool:
        """Check if a Docker image is pulled locally (with timeout)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "image", "inspect", image,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=10)
            return proc.returncode == 0
        except (asyncio.TimeoutError, Exception):
            return False

    # ──── Kernel Lifecycle ────

    async def launch_kernel(
        self, language: str, notebook_id: str | None = None, resource_profile: str = "default"
    ) -> dict:
        lang_lower = language.lower()
        kernel_spec = KERNEL_REGISTRY.get(lang_lower)
        if not kernel_spec:
            raise ValueError(f"Unsupported language: {language}. Available: {list(KERNEL_REGISTRY.keys())}")

        kernel_id = str(uuid.uuid4())
        kernel = KernelInstance(kernel_id=kernel_id, language=lang_lower)
        kernel.status = "idle"

        self._kernels[kernel_id] = kernel
        self._language_kernels.setdefault(lang_lower, []).append(kernel_id)
        return kernel.to_dict()

    def list_kernels(self) -> list[dict]:
        return [k.to_dict() for k in self._kernels.values()]

    def get_kernel(self, kernel_id: str) -> dict | None:
        kernel = self._kernels.get(kernel_id)
        return kernel.to_dict() if kernel else None

    async def execute_code(
        self, kernel_id: str | None, code: str, language: str = "python"
    ) -> AsyncGenerator[dict, None]:
        lang_lower = language.lower()
        kernel_spec = KERNEL_REGISTRY.get(lang_lower)
        if not kernel_spec:
            yield {"type": "error", "ename": "UnsupportedLanguage", "evalue": f"No kernel for '{language}'", "traceback": []}
            return

        kernel = self._kernels.get(kernel_id) if kernel_id else None
        if not kernel:
            result = await self.launch_kernel(language)
            kernel = self._kernels[result["id"]]

        kernel.status = "busy"
        kernel.last_activity = datetime.now(timezone.utc)
        kernel.execution_count += 1

        try:
            docker_image = kernel_spec.get("docker_image", "")
            use_docker = (
                self.docker_available
                and docker_image
                and await self._docker_image_exists(docker_image)
            )

            if use_docker:
                async for output in self._execute_docker(kernel, kernel_spec, code):
                    yield output
            else:
                async for output in self._execute_subprocess(kernel, kernel_spec, code):
                    yield output
        except Exception as e:
            yield {"type": "error", "ename": type(e).__name__, "evalue": str(e), "traceback": []}
        finally:
            kernel.status = "idle"

    # ──── Docker Execution (Enterprise / Colab-style) ────

    async def _execute_docker(
        self, kernel: KernelInstance, spec: dict, code: str
    ) -> AsyncGenerator[dict, None]:
        """Execute code inside an isolated Docker container."""
        from backend.core.config import settings

        file_ext = spec.get("file_extension", ".txt")
        docker_image = spec["docker_image"]
        data_dir = os.path.abspath("data")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_ext, delete=False, dir=data_dir
        ) as f:
            f.write(code)
            temp_path = f.name
            temp_name = os.path.basename(temp_path)

        try:
            # Base docker run args: isolated, resource-limited
            base_args = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", str(settings.default_memory_limit),
                "--cpus", str(settings.default_cpu_limit),
                "--pids-limit", "256",
                "-v", f"{data_dir}:/workspace:rw",
                "-w", "/workspace",
                docker_image,
            ]

            compile_cmd = spec.get("compile_cmd")
            run_cmd = spec.get("run_cmd")

            # For compiled languages, run compile + execute in one shell command
            if compile_cmd:
                compile_parts = " ".join(
                    c.replace("{file}", f"/workspace/{temp_name}")
                     .replace("{output}", f"/workspace/{temp_name}.out")
                    for c in compile_cmd
                )
                if run_cmd:
                    run_parts = " ".join(
                        c.replace("{file}", f"/workspace/{temp_name}")
                         .replace("{output}", f"/workspace/{temp_name}.out")
                        for c in run_cmd
                    )
                else:
                    run_parts = f"/workspace/{temp_name}.out"

                cmd = base_args + ["bash", "-c", f"{compile_parts} && {run_parts}"]
            elif run_cmd:
                cmd_parts = [
                    c.replace("{file}", f"/workspace/{temp_name}")
                     .replace("{output}", f"/workspace/{temp_name}.out")
                    for c in run_cmd
                ]
                cmd = base_args + cmd_parts
            else:
                cmd = base_args + [spec.get("binary", "echo"), f"/workspace/{temp_name}"]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_lines, stderr_lines = await asyncio.wait_for(
                    asyncio.gather(
                        self._collect_stream(proc.stdout, "stdout"),
                        self._collect_stream(proc.stderr, "stderr"),
                    ),
                    timeout=settings.kernel_timeout,
                )
                await asyncio.wait_for(proc.wait(), timeout=10)
            except asyncio.TimeoutError:
                proc.kill()
                yield {"type": "error", "ename": "TimeoutError", "evalue": "Execution timed out", "traceback": []}
                return

            for line in stdout_lines:
                yield {"type": "stream", "name": "stdout", "text": line}
            for line in stderr_lines:
                yield {"type": "stream", "name": "stderr", "text": line}

            if proc.returncode != 0 and not stderr_lines:
                yield {
                    "type": "error",
                    "ename": "RuntimeError",
                    "evalue": f"Container exited with code {proc.returncode}",
                    "traceback": [],
                }
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            try:
                os.unlink(temp_path + ".out")
            except OSError:
                pass

    # ──── Subprocess Execution (Dev / Fallback) ────

    async def _execute_subprocess(
        self, kernel: KernelInstance, spec: dict, code: str
    ) -> AsyncGenerator[dict, None]:
        """Execute code via local subprocess (no Docker needed)."""
        file_ext = spec.get("file_extension", ".txt")
        compile_cmd = spec.get("compile_cmd")
        run_cmd_template = spec.get("run_cmd")

        data_dir = os.path.abspath("data")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_ext, delete=False, dir=data_dir
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            if compile_cmd:
                cmd = [
                    c.replace("{file}", temp_path).replace("{output}", temp_path + ".out")
                    for c in compile_cmd
                ]
                cmd = self._resolve_cmd(cmd)
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    yield {
                        "type": "error",
                        "ename": "CompilationError",
                        "evalue": stderr.decode("utf-8", errors="replace"),
                        "traceback": [],
                    }
                    return

            if run_cmd_template:
                cmd = [
                    c.replace("{file}", temp_path).replace("{output}", temp_path + ".out")
                    for c in run_cmd_template
                ]
                cmd = self._resolve_cmd(cmd)
            else:
                binary = self._resolve_binary(spec.get("binary", "echo"))
                cmd = [binary, temp_path]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_lines, stderr_lines = await asyncio.gather(
                self._collect_stream(proc.stdout, "stdout"),
                self._collect_stream(proc.stderr, "stderr"),
            )
            await proc.wait()

            for line in stdout_lines:
                yield {"type": "stream", "name": "stdout", "text": line}
            for line in stderr_lines:
                yield {"type": "stream", "name": "stderr", "text": line}

            if proc.returncode != 0 and not stderr_lines:
                yield {
                    "type": "error",
                    "ename": "RuntimeError",
                    "evalue": f"Process exited with code {proc.returncode}",
                    "traceback": [],
                }
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            try:
                os.unlink(temp_path + ".out")
            except OSError:
                pass

    # ──── Helpers ────

    def _resolve_binary(self, binary: str) -> str:
        """Resolve a binary name to a full path.
        Special handling for python to use the current interpreter."""
        if binary in ("python", "python3"):
            return sys.executable
        found = shutil.which(binary)
        return found if found else binary

    def _resolve_cmd(self, cmd: list[str]) -> list[str]:
        """Resolve the executable in a command list to its full path."""
        if not cmd:
            return cmd
        exe = cmd[0]
        # Don't resolve paths, placeholders, or relative refs
        if os.sep in exe or '/' in exe or exe.startswith("{") or exe.startswith("."):
            return cmd
        resolved = self._resolve_binary(exe)
        return [resolved] + cmd[1:]

    async def _collect_stream(self, stream, name: str) -> list[str]:
        lines = []
        while True:
            line = await stream.readline()
            if not line:
                break
            lines.append(line.decode("utf-8", errors="replace"))
        return lines

    async def interrupt_kernel(self, kernel_id: str) -> bool:
        kernel = self._kernels.get(kernel_id)
        if not kernel:
            return False
        if kernel._process and kernel._process.returncode is None:
            kernel._process.terminate()
        kernel.status = "idle"
        return True

    async def restart_kernel(self, kernel_id: str) -> dict | None:
        kernel = self._kernels.get(kernel_id)
        if not kernel:
            return None
        await self.shutdown_kernel(kernel_id)
        return await self.launch_kernel(kernel.language)

    async def shutdown_kernel(self, kernel_id: str) -> bool:
        kernel = self._kernels.get(kernel_id)
        if not kernel:
            return False
        if kernel._process and kernel._process.returncode is None:
            kernel._process.terminate()
            try:
                await asyncio.wait_for(kernel._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                kernel._process.kill()
        kernel.status = "dead"
        del self._kernels[kernel_id]
        lang_list = self._language_kernels.get(kernel.language, [])
        if kernel_id in lang_list:
            lang_list.remove(kernel_id)
        return True

    async def get_completions(self, kernel_id: str | None, code: str, cursor_pos: int) -> list[str]:
        return []

    def get_available_languages(self) -> list[dict]:
        result = []
        for lang, spec in KERNEL_REGISTRY.items():
            result.append({
                "language": lang,
                "display_name": spec.get("display_name", lang.title()),
                "file_extension": spec.get("file_extension", ""),
                "mime_type": spec.get("mime_type", "text/plain"),
                "docker_image": spec.get("docker_image", ""),
                "icon": spec.get("icon", ""),
                "docker_available": self.docker_available,
            })
        return result

    def get_execution_mode(self) -> str:
        """Return the current execution backend."""
        return "docker" if self.docker_available else "subprocess"


kernel_manager = KernelManager()
