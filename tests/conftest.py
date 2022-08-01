import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine
from app.deps import get_session
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def override_get_session() -> AsyncSession:
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


@pytest_asyncio.fixture(scope="function")
async def client(override_get_session) -> AsyncClient:
    app.dependency_overrides[get_session] = lambda: override_get_session
    async with AsyncClient(
        app=app,
        base_url="http://localhost:8000",
        headers={"Content-Type": "application/json"},
    ) as _client:
        yield _client
