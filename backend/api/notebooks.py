"""Notebook CRUD API endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from backend.schemas import (
    NotebookCreate, NotebookUpdate, NotebookResponse,
    CellCreate, CellUpdate, CellResponse,
)

router = APIRouter()

# In-memory stores for dev. Replaced by DB in production.
_notebooks: dict[str, dict] = {}
_cells: dict[str, dict] = {}


@router.post("/", response_model=NotebookResponse, status_code=status.HTTP_201_CREATED)
async def create_notebook(nb: NotebookCreate):
    nb_id = str(uuid.uuid4())
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
    return record


@router.get("/", response_model=list[NotebookResponse])
async def list_notebooks():
    return list(_notebooks.values())


@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(notebook_id: str):
    nb = _notebooks.get(notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    # Attach cells
    nb["cells"] = sorted(
        [c for c in _cells.values() if c["notebook_id"] == notebook_id],
        key=lambda c: c["position"],
    )
    return nb


@router.patch("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(notebook_id: str, update: NotebookUpdate):
    nb = _notebooks.get(notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        nb[field] = value
    nb["updated_at"] = datetime.now(timezone.utc)
    return nb


@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notebook(notebook_id: str):
    if notebook_id not in _notebooks:
        raise HTTPException(status_code=404, detail="Notebook not found")
    del _notebooks[notebook_id]
    # Delete associated cells
    to_delete = [cid for cid, c in _cells.items() if c["notebook_id"] == notebook_id]
    for cid in to_delete:
        del _cells[cid]


# ──── Cell endpoints ────

@router.post("/{notebook_id}/cells", response_model=CellResponse, status_code=201)
async def create_cell(notebook_id: str, cell: CellCreate):
    if notebook_id not in _notebooks:
        raise HTTPException(status_code=404, detail="Notebook not found")

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
async def update_cell(notebook_id: str, cell_id: str, update: CellUpdate):
    cell = _cells.get(cell_id)
    if not cell or cell["notebook_id"] != notebook_id:
        raise HTTPException(status_code=404, detail="Cell not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        cell[field] = value
    cell["updated_at"] = datetime.now(timezone.utc)
    return cell


@router.delete("/{notebook_id}/cells/{cell_id}", status_code=204)
async def delete_cell(notebook_id: str, cell_id: str):
    cell = _cells.get(cell_id)
    if not cell or cell["notebook_id"] != notebook_id:
        raise HTTPException(status_code=404, detail="Cell not found")
    del _cells[cell_id]
