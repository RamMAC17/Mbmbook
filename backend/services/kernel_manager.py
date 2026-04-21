"""
Kernel Manager - Multi-language kernel lifecycle management.

Supports Docker-containerized execution with subprocess fallback.
"""

import asyncio
import os
import sys
import re
import shutil
import time
import uuid
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator
from backend.services.kernel_registry import KERNEL_REGISTRY
from backend.services.shared_folder import get_shared_folder_host_path


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


def _safe_scope_id(raw: str | None) -> str:
    """Sanitize an identifier for filesystem/docker path usage."""
    value = raw or "default"
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    return cleaned[:96] if cleaned else "default"


def _to_docker_mount_path(path: str) -> str:
    """Normalize a host path for docker bind mount args."""
    return path.replace("\\", "/").rstrip("/")


class KernelInstance:
    """Represents a running kernel instance."""

    def __init__(
        self,
        kernel_id: str,
        language: str,
        node_id: str | None = None,
        notebook_id: str | None = None,
    ):
        self.id = kernel_id
        self.language = language
        self.node_id = node_id
        self.notebook_id = notebook_id
        self.container_id: str | None = None
        self.workspace_dir: str | None = None
        self.shared_mount_source: str | None = None
        self.status: str = "starting"
        self.started_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.resource_usage: dict = {}
        self.execution_count = 0
        self._process: asyncio.subprocess.Process | None = None
        self.state_history: list[str] = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "language": self.language,
            "status": self.status,
            "node_id": self.node_id,
            "notebook_id": self.notebook_id,
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
        self._notebook_language_kernels: dict[tuple[str, str], str] = {}
        self._docker_ok: bool | None = None
        self._docker_checked_at: float = 0
        self._last_storage_cleanup: float = 0

    @property
    def docker_available(self) -> bool:
        now = time.monotonic()
        if self._docker_ok is None or (now - self._docker_checked_at) > 60:
            self._docker_ok = _docker_available()
            self._docker_checked_at = now
        return self._docker_ok

    async def _docker_image_exists(self, image: str) -> bool:
        import subprocess as _sp

        try:
            result = await asyncio.to_thread(
                _sp.run,
                ["docker", "image", "inspect", image],
                stdout=_sp.DEVNULL,
                stderr=_sp.DEVNULL,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _register_kernel_mapping(self, kernel: KernelInstance) -> None:
        if kernel.notebook_id:
            self._notebook_language_kernels[(kernel.notebook_id, kernel.language)] = kernel.id

    def _unregister_kernel_mapping(self, kernel: KernelInstance) -> None:
        if kernel.notebook_id:
            key = (kernel.notebook_id, kernel.language)
            if self._notebook_language_kernels.get(key) == kernel.id:
                self._notebook_language_kernels.pop(key, None)

    async def launch_kernel(
        self, language: str, notebook_id: str | None = None, resource_profile: str = "default"
    ) -> dict:
        lang_lower = language.lower()
        kernel_spec = KERNEL_REGISTRY.get(lang_lower)
        if not kernel_spec:
            raise ValueError(f"Unsupported language: {language}. Available: {list(KERNEL_REGISTRY.keys())}")

        kernel_id = str(uuid.uuid4())
        kernel = KernelInstance(
            kernel_id=kernel_id,
            language=lang_lower,
            notebook_id=notebook_id,
        )
        kernel.status = "idle"

        self._kernels[kernel_id] = kernel
        self._language_kernels.setdefault(lang_lower, []).append(kernel_id)
        self._register_kernel_mapping(kernel)
        return kernel.to_dict()

    def list_kernels(self) -> list[dict]:
        return [k.to_dict() for k in self._kernels.values()]

    def get_kernel(self, kernel_id: str) -> dict | None:
        kernel = self._kernels.get(kernel_id)
        return kernel.to_dict() if kernel else None

    def _resolve_kernel(
        self,
        kernel_id: str | None,
        language: str,
        notebook_id: str | None,
    ) -> KernelInstance | None:
        kernel = self._kernels.get(kernel_id) if kernel_id else None
        if kernel is None and notebook_id:
            mapped = self._notebook_language_kernels.get((notebook_id, language))
            if mapped:
                kernel = self._kernels.get(mapped)
        return kernel

    async def execute_code(
        self,
        kernel_id: str | None,
        code: str,
        language: str = "python",
        notebook_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        self._maybe_cleanup_storage()

        lang_lower = language.lower()
        kernel_spec = KERNEL_REGISTRY.get(lang_lower)
        if not kernel_spec:
            yield {
                "type": "error",
                "ename": "UnsupportedLanguage",
                "evalue": f"No kernel for '{language}'",
                "traceback": [],
            }
            return

        kernel = self._resolve_kernel(kernel_id, lang_lower, notebook_id)
        if kernel and kernel.language != lang_lower:
            yield {
                "type": "error",
                "ename": "KernelLanguageMismatch",
                "evalue": "Requested language does not match kernel language",
                "traceback": [],
            }
            return

        if kernel and notebook_id:
            if kernel.notebook_id and kernel.notebook_id != notebook_id:
                yield {
                    "type": "error",
                    "ename": "NotebookIsolationError",
                    "evalue": "Kernel belongs to a different notebook",
                    "traceback": [],
                }
                return
            if not kernel.notebook_id:
                kernel.notebook_id = notebook_id
                self._register_kernel_mapping(kernel)

        if not kernel:
            result = await self.launch_kernel(language, notebook_id=notebook_id)
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

    def _kernel_dirs(self, kernel: KernelInstance) -> tuple[str, str, str]:
        scope_id = _safe_scope_id(kernel.notebook_id or kernel.id)
        notebook_data_dir = os.path.abspath(os.path.join("data", "notebooks", scope_id))
        upload_data_dir = os.path.abspath(os.path.join("data", "uploads", scope_id))
        os.makedirs(notebook_data_dir, exist_ok=True)
        os.makedirs(upload_data_dir, exist_ok=True)
        return scope_id, notebook_data_dir, upload_data_dir

    def _get_shared_mount_source(self) -> str:
        return (get_shared_folder_host_path() or "").strip()

    async def _docker_container_running(self, container_id: str) -> bool:
        import subprocess as _sp

        if not container_id:
            return False
        try:
            result = await asyncio.to_thread(
                _sp.run,
                ["docker", "inspect", "-f", "{{.State.Running}}", container_id],
                capture_output=True,
                timeout=8,
            )
            return result.returncode == 0 and result.stdout.decode("utf-8", errors="replace").strip() == "true"
        except Exception:
            return False

    async def _stop_kernel_container(self, kernel: KernelInstance) -> None:
        import subprocess as _sp

        if not kernel.container_id:
            return
        container_id = kernel.container_id
        kernel.container_id = None
        kernel.workspace_dir = None
        kernel.shared_mount_source = None
        try:
            await asyncio.to_thread(
                _sp.run,
                ["docker", "rm", "-f", container_id],
                stdout=_sp.DEVNULL,
                stderr=_sp.DEVNULL,
                timeout=10,
            )
        except Exception:
            pass

    async def _ensure_kernel_container(self, kernel: KernelInstance, spec: dict) -> None:
        import subprocess as _sp
        from backend.core.config import settings

        desired_shared_source = self._get_shared_mount_source()
        running = bool(kernel.container_id) and await self._docker_container_running(kernel.container_id or "")
        shared_changed = (kernel.shared_mount_source or "") != desired_shared_source
        if running and not shared_changed:
            return

        if kernel.container_id:
            await self._stop_kernel_container(kernel)

        scope_id, notebook_data_dir, upload_data_dir = self._kernel_dirs(kernel)
        host_data_dir = (settings.host_data_dir or os.getenv("MBM_HOST_DATA_DIR", "")).strip()
        parent_container = os.getenv("HOSTNAME", "")
        in_container = os.path.exists("/.dockerenv")

        workspace_dir = "/workspace"
        run_cmd: list[str] = [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            f"mbmbook-kernel-{kernel.id[:12]}",
            "--label",
            "mbmbook.kernel=1",
            "--label",
            f"mbmbook.kernel_id={kernel.id}",
            "--network",
            settings.docker_network,
            "--memory",
            str(settings.default_memory_limit),
            "--cpus",
            str(settings.default_cpu_limit),
            "--pids-limit",
            "256",
        ]

        if self._has_nvidia_docker():
            run_cmd += ["--gpus", "all", "-e", "NVIDIA_VISIBLE_DEVICES=all"]

        if host_data_dir:
            host_base = _to_docker_mount_path(host_data_dir)
            host_notebook_dir = f"{host_base}/notebooks/{scope_id}"
            host_upload_dir = f"{host_base}/uploads/{scope_id}"
            run_cmd += [
                "-v",
                f"{host_notebook_dir}:{workspace_dir}:rw",
                "-v",
                f"{host_upload_dir}:/uploads:rw",
            ]
        elif in_container and parent_container:
            workspace_dir = f"/app/data/notebooks/{scope_id}"
            run_cmd += ["--volumes-from", parent_container]
        else:
            run_cmd += [
                "-v",
                f"{notebook_data_dir}:{workspace_dir}:rw",
                "-v",
                f"{upload_data_dir}:/uploads:rw",
            ]

        if desired_shared_source:
            run_cmd += ["-v", f"{_to_docker_mount_path(desired_shared_source)}:/shared:ro"]

        run_cmd += [
            "-w",
            workspace_dir,
            spec["docker_image"],
            "sleep",
            "infinity",
        ]

        result = await asyncio.to_thread(
            _sp.run,
            run_cmd,
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            stderr_text = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(stderr_text or "Failed to start kernel container")

        kernel.container_id = result.stdout.decode("utf-8", errors="replace").strip()
        kernel.workspace_dir = workspace_dir
        kernel.shared_mount_source = desired_shared_source

    def _append_python_history(self, kernel: KernelInstance, code: str) -> None:
        from backend.core.config import settings

        kernel.state_history.append(code)
        limit = max(1, int(settings.python_state_history_limit))
        if len(kernel.state_history) > limit:
            kernel.state_history = kernel.state_history[-limit:]

    def _build_python_stateful_runner(self, history: list[str], code: str) -> str:
        history_payload = repr(history)
        code_payload = repr(code)
        return (
            "import contextlib\n"
            "import io\n"
            "import sys\n"
            "import traceback\n\n"
            f"history = {history_payload}\n"
            f"current = {code_payload}\n"
            "ns = {}\n\n"
            "def _run(src: str, quiet: bool):\n"
            "    stdout_buf = io.StringIO()\n"
            "    stderr_buf = io.StringIO()\n"
            "    try:\n"
            "        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):\n"
            "            exec(compile(src, '<cell>', 'exec'), ns, ns)\n"
            "        return True, stdout_buf.getvalue(), stderr_buf.getvalue(), ''\n"
            "    except Exception:\n"
            "        return False, stdout_buf.getvalue(), stderr_buf.getvalue(), traceback.format_exc()\n\n"
            "for src in history:\n"
            "    ok, _out, _err, tb = _run(src, True)\n"
            "    if not ok:\n"
            "        sys.stderr.write('Stored notebook state is invalid. Restart kernel and run cells again.\\n')\n"
            "        sys.stderr.write(tb)\n"
            "        raise SystemExit(2)\n\n"
            "ok, out, err, tb = _run(current, False)\n"
            "if out:\n"
            "    sys.stdout.write(out)\n"
            "if err:\n"
            "    sys.stderr.write(err)\n"
            "if not ok:\n"
            "    sys.stderr.write(tb)\n"
            "    raise SystemExit(1)\n"
        )

    async def _execute_docker(
        self, kernel: KernelInstance, spec: dict, code: str
    ) -> AsyncGenerator[dict, None]:
        import subprocess as _sp
        from backend.core.config import settings

        await self._ensure_kernel_container(kernel, spec)
        _scope_id, notebook_data_dir, _upload_data_dir = self._kernel_dirs(kernel)

        file_ext = spec.get("file_extension", ".txt")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_ext, delete=False, dir=notebook_data_dir
        ) as f:
            f.write(code)
            temp_path = f.name
            temp_name = os.path.basename(temp_path)

        extra_cleanup: list[str] = []
        try:
            workspace_dir = kernel.workspace_dir or "/workspace"
            compile_cmd = spec.get("compile_cmd")
            run_cmd = spec.get("run_cmd")

            if kernel.language == "python" and run_cmd:
                runner_name = f"__mbm_exec_{uuid.uuid4().hex}.py"
                runner_path = os.path.join(notebook_data_dir, runner_name)
                Path(runner_path).write_text(
                    self._build_python_stateful_runner(kernel.state_history, code),
                    encoding="utf-8",
                )
                extra_cleanup.append(runner_path)
                exec_cmd = [
                    "docker",
                    "exec",
                    kernel.container_id or "",
                    "python",
                    "-u",
                    f"{workspace_dir}/{runner_name}",
                ]
            elif compile_cmd:
                compile_parts = " ".join(
                    c.replace("{file}", f"{workspace_dir}/{temp_name}").replace(
                        "{output}", f"{workspace_dir}/{temp_name}.out"
                    )
                    for c in compile_cmd
                )
                if run_cmd:
                    run_parts = " ".join(
                        c.replace("{file}", f"{workspace_dir}/{temp_name}").replace(
                            "{output}", f"{workspace_dir}/{temp_name}.out"
                        )
                        for c in run_cmd
                    )
                else:
                    run_parts = f"{workspace_dir}/{temp_name}.out"
                exec_cmd = [
                    "docker",
                    "exec",
                    kernel.container_id or "",
                    "bash",
                    "-lc",
                    f"{compile_parts} && {run_parts}",
                ]
            elif run_cmd:
                cmd_parts = [
                    c.replace("{file}", f"{workspace_dir}/{temp_name}").replace(
                        "{output}", f"{workspace_dir}/{temp_name}.out"
                    )
                    for c in run_cmd
                ]
                exec_cmd = ["docker", "exec", kernel.container_id or ""] + cmd_parts
            else:
                exec_cmd = [
                    "docker",
                    "exec",
                    kernel.container_id or "",
                    spec.get("binary", "echo"),
                    f"{workspace_dir}/{temp_name}",
                ]

            try:
                result = await asyncio.to_thread(
                    _sp.run,
                    exec_cmd,
                    capture_output=True,
                    timeout=settings.kernel_timeout,
                )
            except _sp.TimeoutExpired:
                yield {
                    "type": "error",
                    "ename": "TimeoutError",
                    "evalue": "Execution timed out",
                    "traceback": [],
                }
                return

            stdout_text = result.stdout.decode("utf-8", errors="replace")
            stderr_text = result.stderr.decode("utf-8", errors="replace")

            if stdout_text:
                for line in stdout_text.splitlines(keepends=True):
                    yield {"type": "stream", "name": "stdout", "text": line}
            if stderr_text:
                for line in stderr_text.splitlines(keepends=True):
                    yield {"type": "stream", "name": "stderr", "text": line}

            if kernel.language == "python" and result.returncode == 0:
                self._append_python_history(kernel, code)

            if result.returncode != 0 and not stderr_text and not stdout_text:
                yield {
                    "type": "error",
                    "ename": "RuntimeError",
                    "evalue": f"Container exited with code {result.returncode}",
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
            for extra in extra_cleanup:
                try:
                    os.unlink(extra)
                except OSError:
                    pass

    async def _execute_subprocess(
        self, kernel: KernelInstance, spec: dict, code: str
    ) -> AsyncGenerator[dict, None]:
        import subprocess as _sp

        file_ext = spec.get("file_extension", ".txt")
        compile_cmd = spec.get("compile_cmd")
        run_cmd_template = spec.get("run_cmd")

        _scope_id, data_dir, _upload_data_dir = self._kernel_dirs(kernel)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_ext, delete=False, dir=data_dir
        ) as f:
            f.write(code)
            temp_path = f.name

        extra_cleanup: list[str] = []
        try:
            if kernel.language == "python" and run_cmd_template:
                runner_path = os.path.join(data_dir, f"__mbm_exec_{uuid.uuid4().hex}.py")
                Path(runner_path).write_text(
                    self._build_python_stateful_runner(kernel.state_history, code),
                    encoding="utf-8",
                )
                extra_cleanup.append(runner_path)
                cmd = [self._resolve_binary("python"), "-u", runner_path]
            else:
                if compile_cmd:
                    cmd = [
                        c.replace("{file}", temp_path).replace("{output}", temp_path + ".out")
                        for c in compile_cmd
                    ]
                    cmd = self._resolve_cmd(cmd)
                    try:
                        result = await asyncio.to_thread(
                            _sp.run,
                            cmd,
                            capture_output=True,
                            timeout=60,
                        )
                    except FileNotFoundError:
                        binary = cmd[0] if cmd else "unknown"
                        yield {
                            "type": "error",
                            "ename": "CompilerNotFound",
                            "evalue": f"'{binary}' is not installed on the server. Ask the admin to install it.",
                            "traceback": [],
                        }
                        return
                    if result.returncode != 0:
                        yield {
                            "type": "error",
                            "ename": "CompilationError",
                            "evalue": result.stderr.decode("utf-8", errors="replace"),
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

            result = await asyncio.to_thread(
                _sp.run,
                cmd,
                capture_output=True,
                timeout=120,
            )

            stdout_text = result.stdout.decode("utf-8", errors="replace")
            stderr_text = result.stderr.decode("utf-8", errors="replace")

            if stdout_text:
                for line in stdout_text.splitlines(keepends=True):
                    yield {"type": "stream", "name": "stdout", "text": line}
            if stderr_text:
                for line in stderr_text.splitlines(keepends=True):
                    yield {"type": "stream", "name": "stderr", "text": line}

            if kernel.language == "python" and result.returncode == 0:
                self._append_python_history(kernel, code)

            if result.returncode != 0 and not stderr_text and not stdout_text:
                yield {
                    "type": "error",
                    "ename": "RuntimeError",
                    "evalue": f"Process exited with code {result.returncode}",
                    "traceback": [],
                }
        except FileNotFoundError:
            binary = cmd[0] if cmd else "unknown"
            yield {
                "type": "error",
                "ename": "CompilerNotFound",
                "evalue": f"'{binary}' is not installed on the server. Ask the admin to install it.",
                "traceback": [],
            }
        except _sp.TimeoutExpired:
            yield {
                "type": "error",
                "ename": "TimeoutError",
                "evalue": "Execution timed out",
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
            for extra in extra_cleanup:
                try:
                    os.unlink(extra)
                except OSError:
                    pass

    def _cleanup_temp_files(self, directory: Path, stale_seconds: int) -> None:
        now = time.time()
        for child in directory.iterdir():
            if not child.is_file():
                continue
            name = child.name
            is_temp = (
                name.startswith("tmp")
                or name.startswith("__mbm_exec_")
                or name.endswith(".out")
            )
            if not is_temp:
                continue
            try:
                age = now - child.stat().st_mtime
            except OSError:
                continue
            if age > stale_seconds:
                try:
                    child.unlink(missing_ok=True)
                except OSError:
                    pass

    def _maybe_cleanup_storage(self) -> None:
        from backend.core.config import settings

        now_monotonic = time.monotonic()
        if (now_monotonic - self._last_storage_cleanup) < max(
            settings.storage_cleanup_interval_seconds, 30
        ):
            return
        self._last_storage_cleanup = now_monotonic

        stale_seconds = max(1, settings.storage_stale_hours) * 3600
        active_scopes = {
            _safe_scope_id(kernel.notebook_id or kernel.id)
            for kernel in self._kernels.values()
        }

        for base_dir in (Path("data/notebooks"), Path("data/uploads")):
            if not base_dir.exists():
                continue
            for child in base_dir.iterdir():
                if not child.is_dir():
                    continue
                if child.name in active_scopes:
                    self._cleanup_temp_files(child, stale_seconds)
                    continue
                try:
                    age = time.time() - child.stat().st_mtime
                except OSError:
                    continue
                if age > stale_seconds:
                    shutil.rmtree(child, ignore_errors=True)

    def _has_nvidia_docker(self) -> bool:
        """Check if NVIDIA Container Toolkit is available for GPU pass-through."""
        if not hasattr(self, "_nvidia_docker_ok"):
            import subprocess as _sp

            try:
                result = _sp.run(
                    ["docker", "run", "--rm", "--gpus", "all", "hello-world"],
                    capture_output=True,
                    timeout=15,
                )
                self._nvidia_docker_ok = result.returncode == 0
            except Exception:
                self._nvidia_docker_ok = False
        return self._nvidia_docker_ok

    def _resolve_binary(self, binary: str) -> str:
        if binary in ("python", "python3"):
            return sys.executable
        found = shutil.which(binary)
        return found if found else binary

    def _resolve_cmd(self, cmd: list[str]) -> list[str]:
        if not cmd:
            return cmd
        exe = cmd[0]
        if os.sep in exe or "/" in exe or exe.startswith("{") or exe.startswith("."):
            return cmd
        resolved = self._resolve_binary(exe)
        return [resolved] + cmd[1:]

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
        language = kernel.language
        notebook_id = kernel.notebook_id
        await self.shutdown_kernel(kernel_id)
        return await self.launch_kernel(language, notebook_id=notebook_id)

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

        await self._stop_kernel_container(kernel)

        kernel.status = "dead"
        self._unregister_kernel_mapping(kernel)
        del self._kernels[kernel_id]
        lang_list = self._language_kernels.get(kernel.language, [])
        if kernel_id in lang_list:
            lang_list.remove(kernel_id)
        return True

    async def shutdown_all_kernels(self) -> None:
        kernel_ids = list(self._kernels.keys())
        for kernel_id in kernel_ids:
            await self.shutdown_kernel(kernel_id)

    async def get_completions(self, kernel_id: str | None, code: str, cursor_pos: int) -> list[str]:
        return []

    def get_available_languages(self) -> list[dict]:
        result = []
        for lang, spec in KERNEL_REGISTRY.items():
            result.append(
                {
                    "language": lang,
                    "display_name": spec.get("display_name", lang.title()),
                    "file_extension": spec.get("file_extension", ""),
                    "mime_type": spec.get("mime_type", "text/plain"),
                    "docker_image": spec.get("docker_image", ""),
                    "icon": spec.get("icon", ""),
                    "docker_available": self.docker_available,
                }
            )
        return result

    def get_execution_mode(self) -> str:
        return "docker" if self.docker_available else "subprocess"


kernel_manager = KernelManager()
