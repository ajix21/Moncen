import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from database import get_db
from models.event import Event, EventResponse, EventsPage

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events", response_model=EventsPage)
async def list_events(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    cctv_id: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Event)
    count_query = select(func.count()).select_from(Event)

    if cctv_id:
        query = query.where(Event.cctv_id == cctv_id)
        count_query = count_query.where(Event.cctv_id == cctv_id)
    if level:
        query = query.where(Event.alert_level == level.upper())
        count_query = count_query.where(Event.alert_level == level.upper())

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * limit
    query = query.order_by(Event.timestamp.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return EventsPage(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )


@router.delete("/events", status_code=204)
async def clear_events(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Event))
    await db.commit()


@router.get("/stats/summary")
async def stats_summary(db: AsyncSession = Depends(get_db)):
    from models.cctv import CCTVStream

    total_streams = await db.execute(select(func.count()).select_from(CCTVStream))
    enabled_streams = await db.execute(
        select(func.count()).select_from(CCTVStream).where(CCTVStream.enabled == True)
    )
    total_events = await db.execute(select(func.count()).select_from(Event))

    latest_events_result = await db.execute(
        select(Event).order_by(Event.timestamp.desc()).limit(5)
    )
    latest_events = latest_events_result.scalars().all()

    level_counts = {}
    for level in ["NORMAL", "WASPADA", "SIAGA", "DARURAT"]:
        r = await db.execute(
            select(func.count()).select_from(Event).where(Event.alert_level == level)
        )
        level_counts[level.lower()] = r.scalar_one()

    return {
        "total_streams": total_streams.scalar_one(),
        "enabled_streams": enabled_streams.scalar_one(),
        "total_events": total_events.scalar_one(),
        "level_counts": level_counts,
        "latest_events": [EventResponse.model_validate(e) for e in latest_events],
    }
