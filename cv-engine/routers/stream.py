import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

_all_connections: Set[WebSocket] = set()
_cctv_connections: dict[str, Set[WebSocket]] = {}


async def broadcast_cv_result(result: dict):
    payload = json.dumps(result, default=str)
    cctv_id = result.get("cctv_id", "")

    dead_all = set()
    for ws in list(_all_connections):
        try:
            await ws.send_text(payload)
        except Exception:
            dead_all.add(ws)
    _all_connections.difference_update(dead_all)

    dead_cctv = set()
    for ws in list(_cctv_connections.get(cctv_id, set())):
        try:
            await ws.send_text(payload)
        except Exception:
            dead_cctv.add(ws)
    if cctv_id in _cctv_connections:
        _cctv_connections[cctv_id].difference_update(dead_cctv)


@router.websocket("/ws/cv/all")
async def ws_all(websocket: WebSocket):
    await websocket.accept()
    _all_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _all_connections.discard(websocket)
    except Exception:
        _all_connections.discard(websocket)


@router.websocket("/ws/cv/{cctv_id}")
async def ws_cctv(websocket: WebSocket, cctv_id: str):
    await websocket.accept()
    _cctv_connections.setdefault(cctv_id, set()).add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _cctv_connections.get(cctv_id, set()).discard(websocket)
    except Exception:
        _cctv_connections.get(cctv_id, set()).discard(websocket)
