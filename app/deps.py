from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
