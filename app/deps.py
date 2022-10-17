from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async_session: AsyncSession = async_session_factory()  # type: ignore
    try:
        yield async_session
    finally:
        await async_session.close()