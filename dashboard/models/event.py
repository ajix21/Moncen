import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel

from database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cctv_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    cctv_name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    alert_level: Mapped[str] = mapped_column(String, nullable=False)
    alert_color: Mapped[str] = mapped_column(String, nullable=False)
    person_count: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_avg: Mapped[float] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


class EventResponse(BaseModel):
    id: str
    cctv_id: str
    cctv_name: str
    location: str
    alert_level: str
    alert_color: str
    person_count: int
    confidence_avg: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True


class EventsPage(BaseModel):
    items: list[EventResponse]
    total: int
    page: int
    limit: int
    pages: int
