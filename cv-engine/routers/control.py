from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from services.stream_manager import stream_manager

router = APIRouter(prefix="/cv", tags=["control"])


class CVSettings(BaseModel):
    cv_frame_interval: Optional[int] = None
    max_concurrent_streams: Optional[int] = None
    yolo_model_name: Optional[str] = None
    rotation_interval: Optional[int] = None


@router.get("/streams")
async def list_cv_streams():
    return {"streams": stream_manager.get_stream_statuses()}


@router.post("/streams/{cctv_id}/start")
async def start_stream(cctv_id: str):
    ok = await stream_manager.start_stream(cctv_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Stream not found")
    return {"status": "started", "cctv_id": cctv_id}


@router.post("/streams/{cctv_id}/stop")
async def stop_stream(cctv_id: str):
    ok = await stream_manager.stop_stream(cctv_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Stream not found")
    return {"status": "stopped", "cctv_id": cctv_id}


@router.get("/settings")
async def get_settings():
    from config import settings

    return {
        "cv_frame_interval": settings.cv_frame_interval,
        "max_concurrent_streams": settings.max_concurrent_streams,
        "yolo_model_name": settings.yolo_model_name,
        "rotation_interval": settings.rotation_interval,
        "yolo_imgsz": settings.yolo_imgsz,
        "yolo_conf": settings.yolo_conf,
    }


@router.put("/settings")
async def update_settings(payload: CVSettings):
    from config import settings

    if payload.cv_frame_interval is not None:
        settings.cv_frame_interval = payload.cv_frame_interval
    if payload.max_concurrent_streams is not None:
        settings.max_concurrent_streams = payload.max_concurrent_streams
    if payload.yolo_model_name is not None:
        settings.yolo_model_name = payload.yolo_model_name
    if payload.rotation_interval is not None:
        settings.rotation_interval = payload.rotation_interval

    await stream_manager.restart_with_settings()
    return {"status": "applied", "settings": await get_settings()}


@router.get("/snapshot/{cctv_id}")
async def get_snapshot(cctv_id: str):
    from services.stream_manager import stream_manager as sm

    state = sm._streams.get(cctv_id)
    if not state or not state.last_snapshot:
        raise HTTPException(status_code=404, detail="No snapshot available")
    return Response(content=state.last_snapshot, media_type="image/jpeg")
