
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

async_engine: Engine = create_async_engine(
    url=settings.DATABSE_URL_asyncpg,
    echo=False,
    pool_size=4,
    max_overflow=2
)
engine: Engine = create_engine(
    url=settings.DATABASE_URL_psycopg,
    echo=False,
    pool_size=2,
    max_overflow=2
)

session_factory = async_sessionmaker(async_engine)
sync_session_factory = sessionmaker(engine)

class Base(DeclarativeBase):
    pass


async def init_models():
    async with async_engine.begin() as conn:
        if not (echo := async_engine.echo):
            async_engine.echo = True

        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        if not echo:
            async_engine.echo = echo
