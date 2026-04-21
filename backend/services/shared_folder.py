"""Shared folder configuration and lookup helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from backend.core.config import settings


_CONFIG_PATH = settings.data_dir / "shared_folder.json"


def _default_shared_path() -> Path:
    root = (settings.data_dir / "shared").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_config(cfg: dict) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _norm(path_text: str) -> str:
    return path_text.replace("\\", "/").rstrip("/")


def _to_container_path(host_path: str) -> Path:
    host_root = _norm(settings.host_share_root or "")
    host_mount = (settings.host_share_mount or "/hostfs").rstrip("/") or "/hostfs"
    host_norm = _norm(host_path)

    if not host_root:
        raise ValueError("Host share root is not configured")

    if host_norm.lower() == host_root.lower():
        rel = ""
    elif host_norm.lower().startswith(host_root.lower() + "/"):
        rel = host_norm[len(host_root):].lstrip("/")
    else:
        raise ValueError(f"Path must be under configured host root: {host_root}")

    container_path = Path(host_mount)
    if rel:
        container_path = container_path / rel
    return container_path.resolve()


def get_shared_folder_path() -> Path:
    """Return the configured shared folder path visible to the backend."""
    cfg = _load_config()
    configured = str(
        cfg.get("container_path")
        or cfg.get("path")
        or settings.shared_folder_path
        or ""
    ).strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return _default_shared_path()


def get_shared_folder_host_path() -> str:
    """Return a host path suitable for Docker bind-mount source."""
    cfg = _load_config()
    host_path = str(cfg.get("host_path") or "").strip()
    if host_path:
        return host_path

    if settings.shared_folder_path:
        return settings.shared_folder_path

    base = (settings.host_data_dir or "").strip()
    if not base:
        return ""
    return _norm(base) + "/shared"


def set_shared_folder_path(path: str, updated_by: str = "admin") -> dict:
    host_path = _norm(path.strip())
    container_path = _to_container_path(host_path)
    if not container_path.exists() or not container_path.is_dir():
        raise ValueError("Shared path must be an existing directory")

    cfg = {
        "host_path": host_path,
        "container_path": str(container_path),
        "updated_by": updated_by,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_config(cfg)
    return cfg


def get_shared_folder_state() -> dict:
    path = get_shared_folder_path()
    cfg = _load_config()
    return {
        "path": str(path),
        "host_path": cfg.get("host_path") or get_shared_folder_host_path(),
        "exists": path.exists(),
        "configured": bool(cfg.get("host_path") or cfg.get("path") or settings.shared_folder_path),
        "updated_by": cfg.get("updated_by"),
        "updated_at": cfg.get("updated_at"),
    }
