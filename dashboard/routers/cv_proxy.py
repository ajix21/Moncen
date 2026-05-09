import httpx
from fastapi import APIRouter

from config import settings

router = APIRouter(prefix="/api/cv", tags=["cv-proxy"])


@router.get("/status")
async def cv_status():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{settings.cv_engine_url}/health",
                timeout=settings.cv_status_timeout,
            )
            data = r.json()
            data["running"] = True
            return data
    except Exception:
        return {"running": False, "streams_active": 0, "uptime_seconds": 0}
