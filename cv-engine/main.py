import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from services.stream_manager import stream_manager
from routers.stream import router as stream_router, broadcast_cv_result
from routers.control import router as control_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_started_at = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.cv_engine import check_ffmpeg_available
    if not check_ffmpeg_available():
        logger.warning(
            "FFmpeg tidak ditemukan di PATH. "
            "HLS stream capture akan gagal. "
            "Install FFmpeg: https://ffmpeg.org/download.html"
        )

    stream_manager.set_broadcast_callback(broadcast_cv_result)

    streams_data = await stream_manager.load_streams_from_api()
    await stream_manager.start(streams_data)

    yield

    await stream_manager.shutdown()
    logger.info("CV Engine shut down cleanly")


app = FastAPI(title="Semar Watch CV Engine", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)
app.include_router(control_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "streams_active": stream_manager.active_count,
        "model": settings.yolo_model_name,
        "uptime_seconds": stream_manager.uptime_seconds,
        "running": True,
    }
