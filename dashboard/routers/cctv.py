import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database import get_db
from models.cctv import CCTVStream, CCTVStreamCreate, CCTVStreamUpdate, CCTVStreamResponse

router = APIRouter(prefix="/api/cctvs", tags=["cctvs"])


@router.get("", response_model=List[CCTVStreamResponse])
async def list_cctvs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CCTVStream).order_by(CCTVStream.created_at))
    return result.scalars().all()


@router.post("", response_model=CCTVStreamResponse, status_code=201)
async def create_cctv(payload: CCTVStreamCreate, db: AsyncSession = Depends(get_db)):
    stream = CCTVStream(
        id=str(uuid.uuid4()),
        name=payload.name,
        location=payload.location,
        stream_url=payload.stream_url,
        enabled=payload.enabled,
    )
    db.add(stream)
    await db.commit()
    await db.refresh(stream)
    return stream


@router.put("/{cctv_id}", response_model=CCTVStreamResponse)
async def update_cctv(cctv_id: str, payload: CCTVStreamUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CCTVStream).where(CCTVStream.id == cctv_id))
    stream = result.scalar_one_or_none()
    if stream is None:
        raise HTTPException(status_code=404, detail="CCTV stream not found")

    update_data = payload.model_dump(exclude_none=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    for key, value in update_data.items():
        setattr(stream, key, value)

    await db.commit()
    await db.refresh(stream)
    return stream


@router.delete("/{cctv_id}", status_code=204)
async def delete_cctv(cctv_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CCTVStream).where(CCTVStream.id == cctv_id))
    stream = result.scalar_one_or_none()
    if stream is None:
        raise HTTPException(status_code=404, detail="CCTV stream not found")
    await db.delete(stream)
    await db.commit()


@router.patch("/{cctv_id}/toggle", response_model=CCTVStreamResponse)
async def toggle_cctv(cctv_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CCTVStream).where(CCTVStream.id == cctv_id))
    stream = result.scalar_one_or_none()
    if stream is None:
        raise HTTPException(status_code=404, detail="CCTV stream not found")

    stream.enabled = not stream.enabled
    stream.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(stream)
    return stream
