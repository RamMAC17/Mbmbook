"""Pydantic schemas for API request/response models."""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ──── User Schemas ────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ──── Notebook Schemas ────

class NotebookCreate(BaseModel):
    title: str = "Untitled Notebook"
    description: str | None = None
    default_language: str = "python"


class NotebookUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    default_language: str | None = None
    is_public: bool | None = None


class CellCreate(BaseModel):
    cell_type: str = "code"
    language: str = "python"
    source: str = ""
    position: int
    metadata: dict = {}


class CellUpdate(BaseModel):
    source: str | None = None
    cell_type: str | None = None
    language: str | None = None
    position: int | None = None
    metadata: dict | None = None


class CellResponse(BaseModel):
    id: uuid.UUID
    cell_type: str
    language: str
    source: str
    position: int
    outputs: list
    execution_count: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotebookResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    default_language: str
    is_public: bool
    created_at: datetime
    updated_at: datetime
    cells: list[CellResponse] = []

    model_config = {"from_attributes": True}


# ──── Kernel Schemas ────

class KernelLaunchRequest(BaseModel):
    language: str
    notebook_id: str | None = None
    resource_profile: str = "default"  # default, gpu, high-memory


class KernelResponse(BaseModel):
    id: uuid.UUID
    language: str
    status: str
    node_id: str | None
    resource_usage: dict
    started_at: datetime
    last_activity: datetime

    model_config = {"from_attributes": True}


# ──── Execution Schemas ────

class ExecuteRequest(BaseModel):
    cell_id: uuid.UUID
    code: str
    language: str = "python"
    kernel_id: uuid.UUID | None = None


class ExecuteResponse(BaseModel):
    execution_id: str
    status: str  # queued, running, completed, error
    outputs: list = []


# ──── Cluster Schemas ────

class ClusterNodeResponse(BaseModel):
    id: uuid.UUID
    hostname: str
    ip_address: str
    is_head: bool
    status: str
    cpu_cores: int
    cpu_threads: int
    ram_total_gb: float
    gpu_name: str
    gpu_vram_gb: float
    disk_total_gb: float
    active_kernels: int
    last_heartbeat: datetime | None

    model_config = {"from_attributes": True}


class ClusterStatus(BaseModel):
    total_nodes: int
    online_nodes: int
    total_cpu_cores: int
    total_ram_gb: float
    total_gpu_vram_gb: float
    active_kernels: int
    nodes: list[ClusterNodeResponse]


class ResourceUsage(BaseModel):
    cpu_percent: float
    ram_used_gb: float
    ram_total_gb: float
    gpu_utilization: float | None
    gpu_memory_used_gb: float | None
    gpu_memory_total_gb: float | None
    disk_used_gb: float
    disk_total_gb: float
