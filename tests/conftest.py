from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine
from app.deps import get_session
from app.main import app


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    # establish database connection
    connection = await engine.connect()
    # begin a transaction
    await connection.begin()
    # bind an individual AsyncSession to the connection
    session = AsyncSession(bind=connection)
    try:
        yield session
    finally:
        await session.rollback()
        await connection.close()


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as client:
        yield client
