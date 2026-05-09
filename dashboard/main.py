import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from config import settings
from database import init_db, AsyncSessionLocal
from models.event import Event
from models.cctv import CCTVStream
from routers.cctv import router as cctv_router
from routers.events import router as events_router
from routers.cv_proxy import router as cv_proxy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Semar Watch Dashboard", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cctv_router)
app.include_router(events_router)
app.include_router(cv_proxy_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


class DashboardWSManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, data: dict):
        payload = json.dumps(data, default=str)
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = DashboardWSManager()


@app.websocket("/ws/dash/summary")
async def dashboard_summary_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            async with AsyncSessionLocal() as db:
                total = (await db.execute(select(func.count()).select_from(CCTVStream))).scalar_one()
                enabled = (
                    await db.execute(
                        select(func.count()).select_from(CCTVStream).where(CCTVStream.enabled == True)
                    )
                ).scalar_one()
                latest_events_result = await db.execute(
                    select(Event).order_by(Event.timestamp.desc()).limit(5)
                )
                latest_events = latest_events_result.scalars().all()

            payload = {
                "type": "summary",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_streams": total,
                "enabled_streams": enabled,
                "latest_events": [
                    {
                        "id": e.id,
                        "cctv_id": e.cctv_id,
                        "cctv_name": e.cctv_name,
                        "alert_level": e.alert_level,
                        "alert_color": e.alert_color,
                        "person_count": e.person_count,
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    }
                    for e in latest_events
                ],
            }
            await ws_manager.broadcast(payload)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
