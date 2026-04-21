"""Notebook CRUD API endpoints."""

import uuid
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, status
from backend.core.config import settings
from backend.services.notebook_sessions import (
    bind_or_validate_owner,
    get_owner,
    release_owner,
)
from backend.schemas import (
    NotebookCreate, NotebookUpdate, NotebookResponse,
    CellCreate, CellUpdate, CellResponse,
)

router = APIRouter()

# In-memory stores for dev. Replaced by DB in production.
_notebooks: dict[str, dict] = {}
_cells: dict[str, dict] = {}


def _get_session_id(request: Request) -> str:
    return request.headers.get("x-mbm-session") or (request.client.host if request.client else "anonymous")


def _bind_or_validate_owner(notebook_id: str, session_id: str) -> None:
    if not bind_or_validate_owner(notebook_id, session_id):
        raise HTTPException(status_code=403, detail="Notebook belongs to another user session")


@router.post("/", response_model=NotebookResponse, status_code=status.HTTP_201_CREATED)
async def create_notebook(nb: NotebookCreate, request: Request):
    nb_id = str(uuid.uuid4())
    session_id = _get_session_id(request)
    now = datetime.now(timezone.utc)
    record = {
        "id": nb_id,
        "title": nb.title,
        "description": nb.description,
        "default_language": nb.default_language,
        "is_public": False,
        "created_at": now,
        "updated_at": now,
        "cells": [],
    }
    _notebooks[nb_id] = record
    _bind_or_validate_owner(nb_id, session_id)
    return record


@router.get("/", response_model=list[NotebookResponse])
async def list_notebooks(request: Request):
    session_id = _get_session_id(request)
    return [
        nb for nb_id, nb in _notebooks.items()
        if get_owner(nb_id) == session_id
    ]


@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(notebook_id: str, request: Request):
    nb = _notebooks.get(notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    session_id = _get_session_id(request)
    _bind_or_validate_owner(notebook_id, session_id)
    # Attach cells
    nb["cells"] = sorted(
        [c for c in _cells.values() if c["notebook_id"] == notebook_id],
        key=lambda c: c["position"],
    )
    return nb


@router.patch("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(notebook_id: str, update: NotebookUpdate, request: Request):
    nb = _notebooks.get(notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    session_id = _get_session_id(request)
    _bind_or_validate_owner(notebook_id, session_id)
    for field, value in update.model_dump(exclude_unset=True).items():
        nb[field] = value
    nb["updated_at"] = datetime.now(timezone.utc)
    return nb


@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notebook(notebook_id: str, request: Request):
    if notebook_id not in _notebooks:
        raise HTTPException(status_code=404, detail="Notebook not found")
    session_id = _get_session_id(request)
    _bind_or_validate_owner(notebook_id, session_id)
    del _notebooks[notebook_id]
    release_owner(notebook_id, session_id)

    scope_id = re.sub(r"[^A-Za-z0-9._-]", "_", notebook_id)[:96] or "default"
    shutil.rmtree(settings.uploads_dir / scope_id, ignore_errors=True)
    shutil.rmtree(settings.data_dir / "notebooks" / scope_id, ignore_errors=True)
    # Delete associated cells
    to_delete = [cid for cid, c in _cells.items() if c["notebook_id"] == notebook_id]
    for cid in to_delete:
        del _cells[cid]


# ──── Cell endpoints ────

@router.post("/{notebook_id}/cells", response_model=CellResponse, status_code=201)
async def create_cell(notebook_id: str, cell: CellCreate, request: Request):
    if notebook_id not in _notebooks:
        raise HTTPException(status_code=404, detail="Notebook not found")
    session_id = _get_session_id(request)
    _bind_or_validate_owner(notebook_id, session_id)

    cell_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    record = {
        "id": cell_id,
        "notebook_id": notebook_id,
        "cell_type": cell.cell_type,
        "language": cell.language,
        "source": cell.source,
        "position": cell.position,
        "outputs": [],
        "execution_count": None,
        "created_at": now,
        "updated_at": now,
    }
    _cells[cell_id] = record
    return record


@router.patch("/{notebook_id}/cells/{cell_id}", response_model=CellResponse)
async def update_cell(notebook_id: str, cell_id: str, update: CellUpdate, request: Request):
    cell = _cells.get(cell_id)
    if not cell or cell["notebook_id"] != notebook_id:
        raise HTTPException(status_code=404, detail="Cell not found")
    session_id = _get_session_id(request)
    _bind_or_validate_owner(notebook_id, session_id)
    for field, value in update.model_dump(exclude_unset=True).items():
        cell[field] = value
    cell["updated_at"] = datetime.now(timezone.utc)
    return cell


@router.delete("/{notebook_id}/cells/{cell_id}", status_code=204)
async def delete_cell(notebook_id: str, cell_id: str, request: Request):
    cell = _cells.get(cell_id)
    if not cell or cell["notebook_id"] != notebook_id:
        raise HTTPException(status_code=404, detail="Cell not found")
    session_id = _get_session_id(request)
    _bind_or_validate_owner(notebook_id, session_id)
    del _cells[cell_id]


@router.post("/{notebook_id}/uploads", status_code=status.HTTP_201_CREATED)
async def upload_notebook_files(notebook_id: str, request: Request, files: list[UploadFile] = File(...)):
    """Upload one or more files for use in notebook code cells.

    Files are stored under data/uploads/<notebook_id>/ and are accessible
    from Python execution as /uploads/<filename>.
    """
    session_id = _get_session_id(request)
    _bind_or_validate_owner(notebook_id, session_id)

    scope_id = re.sub(r"[^A-Za-z0-9._-]", "_", notebook_id)[:96] or "default"
    upload_dir = settings.uploads_dir / scope_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded: list[dict] = []

    for incoming in files:
        original_name = incoming.filename or "uploaded_file"
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(original_name).name)
        if not safe_name:
            safe_name = f"file_{uuid.uuid4().hex[:8]}"

        target = upload_dir / safe_name
        suffix = 1
        while target.exists():
            stem = Path(safe_name).stem
            ext = Path(safe_name).suffix
            target = upload_dir / f"{stem}_{suffix}{ext}"
            suffix += 1

        content = await incoming.read()
        target.write_bytes(content)

        uploaded.append({
            "name": target.name,
            "size": len(content),
            "path": f"/uploads/{target.name}",
        })

    return {
        "uploaded": uploaded,
        "count": len(uploaded),
        "message": "Files uploaded successfully",
    }
