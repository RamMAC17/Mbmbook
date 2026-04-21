"""Shared notebook session ownership registry."""

from __future__ import annotations

from threading import Lock

_owners: dict[str, str] = {}
_lock = Lock()


def bind_or_validate_owner(notebook_id: str, session_id: str) -> bool:
    """Bind notebook ownership on first use or validate existing ownership."""
    with _lock:
        owner = _owners.get(notebook_id)
        if owner and owner != session_id:
            return False
        _owners.setdefault(notebook_id, session_id)
        return True


def release_owner(notebook_id: str, session_id: str | None = None) -> None:
    """Release ownership if unowned by another active session."""
    with _lock:
        owner = _owners.get(notebook_id)
        if owner is None:
            return
        if session_id is None or owner == session_id:
            _owners.pop(notebook_id, None)


def get_owner(notebook_id: str) -> str | None:
    with _lock:
        return _owners.get(notebook_id)
