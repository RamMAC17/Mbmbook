"""WebSocket endpoint for real-time notebook communication."""

import json
import uuid
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.kernel_manager import kernel_manager

router = APIRouter()

# Active WebSocket connections: {notebook_id: [websocket, ...]}
_connections: dict[str, list[WebSocket]] = {}


@router.websocket("/notebook/{notebook_id}")
async def notebook_ws(websocket: WebSocket, notebook_id: str):
    """
    WebSocket for real-time notebook interaction.

    Messages from client:
      {"type": "execute", "cell_id": "...", "code": "...", "language": "python"}
      {"type": "interrupt", "kernel_id": "..."}
      {"type": "complete", "code": "...", "cursor_pos": 10, "kernel_id": "..."}

    Messages to client:
      {"type": "stream", "cell_id": "...", "name": "stdout", "text": "..."}
      {"type": "execute_result", "cell_id": "...", "data": {...}}
      {"type": "error", "cell_id": "...", "ename": "...", "evalue": "...", "traceback": [...]}
      {"type": "status", "cell_id": "...", "execution_state": "busy|idle"}
      {"type": "kernel_status", "kernel_id": "...", "status": "..."}
    """
    await websocket.accept()
    print(f"  🔌 WebSocket connected: notebook={notebook_id} client={websocket.client}")

    if notebook_id not in _connections:
        _connections[notebook_id] = []
    _connections[notebook_id].append(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")
            print(f"  📨 WS message: type={msg_type} notebook={notebook_id}")

            if msg_type == "execute":
                await _handle_execute(websocket, notebook_id, msg)
            elif msg_type == "interrupt":
                await _handle_interrupt(websocket, msg)
            elif msg_type == "complete":
                await _handle_complete(websocket, msg)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})

    except WebSocketDisconnect:
        _connections[notebook_id].remove(websocket)
        if not _connections[notebook_id]:
            del _connections[notebook_id]
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        _connections.get(notebook_id, [])
        try:
            _connections[notebook_id].remove(websocket)
        except (KeyError, ValueError):
            pass


async def _handle_execute(ws: WebSocket, notebook_id: str, msg: dict):
    """Execute code in a kernel and stream results back."""
    cell_id = msg.get("cell_id", str(uuid.uuid4()))
    code = msg.get("code", "")
    language = msg.get("language", "python")
    kernel_id = msg.get("kernel_id")

    # Notify: execution starting
    await ws.send_json({
        "type": "status",
        "cell_id": cell_id,
        "execution_state": "busy",
    })

    try:
        # Execute via kernel manager
        async for output in kernel_manager.execute_code(
            kernel_id=kernel_id,
            code=code,
            language=language,
        ):
            output["cell_id"] = cell_id
            await ws.send_json(output)

            # Broadcast to other viewers of this notebook
            for conn in _connections.get(notebook_id, []):
                if conn != ws:
                    try:
                        await conn.send_json(output)
                    except Exception:
                        pass

    except Exception as e:
        await ws.send_json({
            "type": "error",
            "cell_id": cell_id,
            "ename": type(e).__name__,
            "evalue": str(e),
            "traceback": [],
        })

    # Notify: execution complete
    await ws.send_json({
        "type": "status",
        "cell_id": cell_id,
        "execution_state": "idle",
    })


async def _handle_interrupt(ws: WebSocket, msg: dict):
    kernel_id = msg.get("kernel_id")
    if kernel_id:
        await kernel_manager.interrupt_kernel(kernel_id)
        await ws.send_json({"type": "kernel_status", "kernel_id": kernel_id, "status": "interrupted"})


async def _handle_complete(ws: WebSocket, msg: dict):
    """Handle code completion requests."""
    code = msg.get("code", "")
    cursor_pos = msg.get("cursor_pos", len(code))
    kernel_id = msg.get("kernel_id")

    completions = await kernel_manager.get_completions(kernel_id, code, cursor_pos)
    await ws.send_json({"type": "complete_reply", "matches": completions})
