
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine: Engine = create_async_engine(
    url=settings.DATABSE_URL_asyncpg,
    echo=False,
    pool_size=4,
    max_overflow=2
)

session_factory = async_sessionmaker(engine)


class Base(DeclarativeBase):
    pass


async def init_models():
    async with engine.begin() as conn:
        if not (echo := engine.echo):
            engine.echo = True

        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        if not echo:
            engine.echo = echo
