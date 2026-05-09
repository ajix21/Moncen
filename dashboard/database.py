import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from config import settings, DEFAULT_CCTV_STREAMS


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        from models.cctv import CCTVStream
        from models.event import Event
        await conn.run_sync(Base.metadata.create_all)

    await _seed_default_streams()


async def _seed_default_streams():
    from models.cctv import CCTVStream
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CCTVStream).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        for data in DEFAULT_CCTV_STREAMS:
            stream = CCTVStream(
                id=data["id"],
                name=data["name"],
                location=data["location"],
                stream_url=data["stream_url"],
                enabled=data["enabled"],
            )
            session.add(stream)

        await session.commit()
