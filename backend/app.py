"""MBM Book - Main FastAPI Application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from backend.core.config import settings
from backend.api.notebooks import router as notebooks_router
from backend.api.kernels import router as kernels_router
from backend.api.cluster import router as cluster_router
from backend.api.ws import router as ws_router
from backend.api.auth import router as auth_router

# Path to the frontend build
FRONTEND_BUILD = Path(__file__).resolve().parent.parent / "frontend" / "dist"


# ──── LAN Access Control Middleware (pure ASGI – works with WebSockets) ────
class LANAccessMiddleware:
    """
    Restricts access to clients on the college LAN subnet only.
    Uses raw ASGI interface so WebSocket connections pass through correctly.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"

            if not settings.is_ip_allowed(client_ip):
                if scope["type"] == "websocket":
                    # Reject WebSocket with policy violation code
                    await send({"type": "websocket.close", "code": 1008})
                    return
                # Reject HTTP
                response = JSONResponse(
                    status_code=403,
                    content={
                        "detail": f"Access denied. Your IP ({client_ip}) is not on the college LAN. "
                                  f"Connect to the college WiFi network to access MBM Book.",
                        "allowed_subnet": settings.allowed_subnet,
                    },
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


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
