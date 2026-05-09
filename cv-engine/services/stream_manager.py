import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class StreamState:
    def __init__(self, cctv_id: str, cctv_name: str, location: str, stream_url: str):
        self.cctv_id = cctv_id
        self.cctv_name = cctv_name
        self.location = location
        self.stream_url = stream_url
        self.cv_status: str = "queued"  # "analyzing" | "queued" | "offline"
        self.last_result: Optional[dict] = None
        self.last_snapshot: Optional[bytes] = None
        self.task: Optional[asyncio.Task] = None
        self.previous_alert_level: Optional[str] = None


class StreamManager:
    def __init__(self):
        self._streams: dict[str, StreamState] = {}
        self._active_ids: list[str] = []
        self._queue: list[str] = []
        self._rotation_task: Optional[asyncio.Task] = None
        self._started_at: float = time.time()
        self._broadcast_callback = None
        self._settings_lock = asyncio.Lock()
        self._db_engine = None
        self._db_session_factory = None

    @property
    def uptime_seconds(self) -> int:
        return int(time.time() - self._started_at)

    @property
    def active_count(self) -> int:
        return len(self._active_ids)

    def set_broadcast_callback(self, cb):
        self._broadcast_callback = cb

    async def load_streams_from_api(self):
        import httpx
        from config import settings

        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{settings.dashboard_url}/api/cctvs", timeout=5.0)
                streams = r.json()
                logger.info(f"Fetched {len(streams)} CCTV streams from dashboard")
                return streams
        except Exception as e:
            logger.warning(f"Dashboard unreachable, loading from DB: {e}")
            return await self._load_streams_from_db()

    async def _load_streams_from_db(self):
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from sqlalchemy import text, select
        from config import settings

        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with SessionLocal() as db:
            result = await db.execute(
                text("SELECT id, name, location, stream_url, enabled FROM cctv_streams WHERE enabled=1")
            )
            rows = result.fetchall()

        await engine.dispose()
        return [
            {"id": r[0], "name": r[1], "location": r[2], "stream_url": r[3], "enabled": bool(r[4])}
            for r in rows
        ]

    async def start(self, streams_data: list[dict]):
        from config import settings

        enabled = [s for s in streams_data if s.get("enabled")]
        for s in enabled:
            self._streams[s["id"]] = StreamState(
                cctv_id=s["id"],
                cctv_name=s["name"],
                location=s["location"],
                stream_url=s["stream_url"],
            )

        ids = list(self._streams.keys())
        max_c = settings.max_concurrent_streams
        self._active_ids = ids[:max_c]
        self._queue = ids[max_c:]

        for sid in self._active_ids:
            await self._start_stream_task(sid)

        for sid in self._queue:
            self._streams[sid].cv_status = "queued"

        if self._queue:
            self._rotation_task = asyncio.create_task(self._rotation_loop())

        logger.info(
            f"CV Engine started — processing {len(self._active_ids)}/{len(ids)} streams "
            f"(max: {max_c})"
        )

    async def _start_stream_task(self, cctv_id: str):
        state = self._streams[cctv_id]
        state.cv_status = "analyzing"
        state.task = asyncio.create_task(self._stream_loop(cctv_id))

    async def _stop_stream_task(self, cctv_id: str):
        state = self._streams.get(cctv_id)
        if state and state.task and not state.task.done():
            state.task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(state.task), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        if state:
            state.cv_status = "queued"
            state.task = None

    async def _rotation_loop(self):
        from config import settings

        while True:
            await asyncio.sleep(settings.rotation_interval)
            if not self._queue:
                continue

            async with self._settings_lock:
                outgoing = list(self._active_ids)
                incoming = self._queue[: settings.max_concurrent_streams]
                remaining = self._queue[settings.max_concurrent_streams :]

                for sid in outgoing:
                    await self._stop_stream_task(sid)

                self._queue = remaining + outgoing
                self._active_ids = incoming

                for sid in incoming:
                    await self._start_stream_task(sid)

                for sid in self._queue:
                    self._streams[sid].cv_status = "queued"

    async def _stream_loop(self, cctv_id: str):
        import asyncio
        from config import settings
        from services.cv_engine import extract_frame_from_hls, run_inference, encode_frame_jpeg
        from services.alert_service import get_alert_level, should_log_event

        state = self._streams[cctv_id]

        while True:
            try:
                frame = await asyncio.get_event_loop().run_in_executor(
                    None, extract_frame_from_hls, state.stream_url
                )
                if frame is None:
                    state.cv_status = "offline"
                    await asyncio.sleep(settings.cv_frame_interval)
                    state.cv_status = "analyzing"
                    continue

                inference = await asyncio.get_event_loop().run_in_executor(
                    None, run_inference, frame
                )

                snapshot = await asyncio.get_event_loop().run_in_executor(
                    None, encode_frame_jpeg, frame
                )

                level, color = get_alert_level(inference["person_count"])

                result = {
                    "type": "cv_result",
                    "cctv_id": cctv_id,
                    "cctv_name": state.cctv_name,
                    "location": state.location,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "person_count": inference["person_count"],
                    "alert_level": level,
                    "alert_color": color,
                    "confidence_avg": inference["confidence_avg"],
                    "stream_status": "active",
                    "cv_status": "analyzing",
                    "frame_width": inference["frame_width"],
                    "frame_height": inference["frame_height"],
                    "bounding_boxes": inference["bounding_boxes"],
                    "processing_time_ms": inference["processing_time_ms"],
                }

                state.last_result = result
                state.last_snapshot = snapshot

                if should_log_event(level, state.previous_alert_level):
                    await self._write_event(result)

                state.previous_alert_level = level

                if self._broadcast_callback:
                    await self._broadcast_callback(result)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stream loop error [{cctv_id}]: {e}")
                await asyncio.sleep(5)

            await asyncio.sleep(settings.cv_frame_interval)

    async def _get_db_session_factory(self):
        if self._db_engine is None:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            from sqlalchemy import text
            from config import settings

            self._db_engine = create_async_engine(settings.database_url, echo=False)
            async with self._db_engine.begin() as conn:
                await conn.execute(text("PRAGMA journal_mode=WAL"))
            self._db_session_factory = async_sessionmaker(
                self._db_engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._db_session_factory

    async def _write_event(self, result: dict):
        from sqlalchemy import text
        import uuid

        SessionLocal = await self._get_db_session_factory()
        async with SessionLocal() as db:
            await db.execute(
                text(
                    "INSERT INTO events (id, cctv_id, cctv_name, location, alert_level, alert_color, "
                    "person_count, confidence_avg, timestamp) VALUES "
                    "(:id, :cctv_id, :cctv_name, :location, :alert_level, :alert_color, "
                    ":person_count, :confidence_avg, :timestamp)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "cctv_id": result["cctv_id"],
                    "cctv_name": result["cctv_name"],
                    "location": result["location"],
                    "alert_level": result["alert_level"],
                    "alert_color": result["alert_color"],
                    "person_count": result["person_count"],
                    "confidence_avg": result["confidence_avg"],
                    "timestamp": result["timestamp"],
                },
            )
            await db.commit()

    async def restart_with_settings(self):
        async with self._settings_lock:
            if self._rotation_task and not self._rotation_task.done():
                self._rotation_task.cancel()

            for sid in list(self._active_ids):
                await self._stop_stream_task(sid)

            from config import settings

            all_ids = list(self._streams.keys())
            max_c = settings.max_concurrent_streams
            self._active_ids = all_ids[:max_c]
            self._queue = all_ids[max_c:]

            for sid in self._active_ids:
                await self._start_stream_task(sid)

            for sid in self._queue:
                self._streams[sid].cv_status = "queued"

            if self._queue:
                self._rotation_task = asyncio.create_task(self._rotation_loop())

    def get_stream_statuses(self) -> list[dict]:
        result = []
        for sid, state in self._streams.items():
            result.append(
                {
                    "cctv_id": sid,
                    "cctv_name": state.cctv_name,
                    "location": state.location,
                    "cv_status": state.cv_status,
                    "last_count": state.last_result["person_count"] if state.last_result else None,
                    "last_level": state.last_result["alert_level"] if state.last_result else None,
                }
            )
        return result

    async def start_stream(self, cctv_id: str) -> bool:
        state = self._streams.get(cctv_id)
        if not state:
            return False
        if state.cv_status == "analyzing":
            return True
        from config import settings

        if len(self._active_ids) >= settings.max_concurrent_streams:
            oldest = self._active_ids.pop(0)
            await self._stop_stream_task(oldest)
            self._queue.append(oldest)

        if cctv_id in self._queue:
            self._queue.remove(cctv_id)
        self._active_ids.append(cctv_id)
        await self._start_stream_task(cctv_id)
        return True

    async def stop_stream(self, cctv_id: str) -> bool:
        state = self._streams.get(cctv_id)
        if not state:
            return False
        await self._stop_stream_task(cctv_id)
        if cctv_id in self._active_ids:
            self._active_ids.remove(cctv_id)
        return True

    async def shutdown(self):
        if self._rotation_task and not self._rotation_task.done():
            self._rotation_task.cancel()
        for sid in list(self._active_ids):
            await self._stop_stream_task(sid)
        if self._db_engine:
            await self._db_engine.dispose()


stream_manager = StreamManager()
