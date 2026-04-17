"""MBM Book - Main FastAPI Application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.config import settings
from backend.api.notebooks import router as notebooks_router
from backend.api.kernels import router as kernels_router
from backend.api.cluster import router as cluster_router
from backend.api.ws import router as ws_router
from backend.api.auth import router as auth_router

# Path to the frontend build
FRONTEND_BUILD = Path(__file__).resolve().parent.parent / "frontend" / "dist"


# ──── LAN Access Control Middleware ────
class LANAccessMiddleware(BaseHTTPMiddleware):
    """
    Restricts access to clients on the college LAN subnet only.
    Subnet: 10.10.12.0/23 (255.255.254.0) — covers 10.10.12.1 - 10.10.13.254
    """

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        if not settings.is_ip_allowed(client_ip):
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Access denied. Your IP ({client_ip}) is not on the college LAN. "
                              f"Connect to the college WiFi network to access MBM Book.",
                    "allowed_subnet": settings.allowed_subnet,
                },
            )

        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"")
    print(f"  ╔══════════════════════════════════════════════════════════╗")
    print(f"  ║               MBM Book v{settings.app_version}                           ║")
    print(f"  ║       Distributed Multi-Language Notebook Platform      ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║  Server  : http://{settings.host_ip}                        ║")
    print(f"  ║  API Docs: http://{settings.host_ip}/docs                   ║")
    print(f"  ║  LAN     : {settings.allowed_subnet} ║")
    print(f"  ╚══════════════════════════════════════════════════════════╝")
    print(f"")

    # Register this PC as a cluster node
    from backend.services.cluster_manager import cluster_manager
    import socket
    hostname = socket.gethostname()
    await cluster_manager.register_node(hostname, settings.host_ip, is_head=True)
    print(f"  ✅ Registered as head node: {hostname} ({settings.host_ip})")
    print(f"")

    yield
    # Shutdown
    print(f"  🛑 Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# LAN access restriction (applied FIRST, before CORS)
app.add_middleware(LANAccessMiddleware)

# CORS - allow all origins since LANAccessMiddleware handles access control
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router, prefix=f"{settings.api_prefix}/auth", tags=["auth"])
app.include_router(notebooks_router, prefix=f"{settings.api_prefix}/notebooks", tags=["notebooks"])
app.include_router(kernels_router, prefix=f"{settings.api_prefix}/kernels", tags=["kernels"])
app.include_router(cluster_router, prefix=f"{settings.api_prefix}/cluster", tags=["cluster"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "host": settings.host_ip,
        "allowed_subnet": settings.allowed_subnet,
    }


# ──── Serve frontend build (SPA) ────
if FRONTEND_BUILD.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_BUILD / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA for all non-API routes."""
        # Try serving the exact file first
        file_path = FRONTEND_BUILD / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Fall back to index.html for SPA routing
        return FileResponse(str(FRONTEND_BUILD / "index.html"))
