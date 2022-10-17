"""
Sets up postgres connection pool.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings


engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, future=True, echo=False)

async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
