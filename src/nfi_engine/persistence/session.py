from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from nfi_engine.persistence.models import Base

SQLITE_ASYNC_PREFIX: Final = "sqlite+aiosqlite:///"


@dataclass(frozen=True, slots=True)
class PersistenceDatabase:
    database_url: str
    engine: AsyncEngine
    session: async_sessionmaker[AsyncSession]

    async def initialize(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        await self.engine.dispose()


def create_persistence_database(database_url: str) -> PersistenceDatabase:
    _ensure_sqlite_parent(database_url)
    engine = create_async_engine(
        database_url,
        future=True,
        poolclass=None if database_url.endswith(":memory:") else NullPool,
    )
    session = async_sessionmaker(engine, expire_on_commit=False)
    return PersistenceDatabase(database_url=database_url, engine=engine, session=session)


def _ensure_sqlite_parent(database_url: str) -> None:
    if not database_url.startswith(SQLITE_ASYNC_PREFIX):
        return
    path_text = database_url.removeprefix(SQLITE_ASYNC_PREFIX)
    if path_text in {"", ":memory:"}:
        return
    Path(path_text).parent.mkdir(parents=True, exist_ok=True)
