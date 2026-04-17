"""SQLAlchemy models for MBM Book."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class KernelStatus(str, enum.Enum):
    STARTING = "starting"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    DEAD = "dead"
    SHUTTING_DOWN = "shutting_down"


class CellType(str, enum.Enum):
    CODE = "code"
    MARKDOWN = "markdown"
    RAW = "raw"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    notebooks = relationship("Notebook", back_populates="owner")


class Notebook(Base):
    __tablename__ = "notebooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, default="Untitled Notebook")
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    default_language = Column(String(50), default="python")
    metadata_ = Column("metadata", JSON, default=dict)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="notebooks")
    cells = relationship("Cell", back_populates="notebook", order_by="Cell.position",
                         cascade="all, delete-orphan")


class Cell(Base):
    __tablename__ = "cells"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notebook_id = Column(UUID(as_uuid=True), ForeignKey("notebooks.id"), nullable=False)
    cell_type = Column(Enum(CellType), default=CellType.CODE)
    language = Column(String(50), default="python")
    source = Column(Text, default="")
    position = Column(Integer, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    outputs = Column(JSON, default=list)
    execution_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    notebook = relationship("Notebook", back_populates="cells")


class KernelSession(Base):
    __tablename__ = "kernel_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notebook_id = Column(UUID(as_uuid=True), ForeignKey("notebooks.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    language = Column(String(50), nullable=False)
    status = Column(Enum(KernelStatus), default=KernelStatus.STARTING)
    node_id = Column(String(255))  # Which cluster node this kernel is on
    container_id = Column(String(255))  # Docker container ID
    connection_info = Column(JSON)  # ZMQ ports etc.
    resource_usage = Column(JSON, default=dict)  # CPU, RAM, GPU usage
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ClusterNode(Base):
    __tablename__ = "cluster_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hostname = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=False)
    port = Column(Integer, default=8786)
    is_head = Column(Boolean, default=False)
    status = Column(String(50), default="offline")  # online, offline, draining
    cpu_cores = Column(Integer, default=20)
    cpu_threads = Column(Integer, default=28)
    ram_total_gb = Column(Float, default=32.0)
    gpu_name = Column(String(255), default="NVIDIA GeForce RTX 3060")
    gpu_vram_gb = Column(Float, default=12.0)
    disk_total_gb = Column(Float, default=512.0)
    active_kernels = Column(Integer, default=0)
    last_heartbeat = Column(DateTime(timezone=True))
    metadata_ = Column("metadata", JSON, default=dict)
