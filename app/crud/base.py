"""
Defines base class with generic logic for CRUD operations.
Every model should inherit this logic and enrich/override it if needed.
"""

from typing import Any, Generic, Type, TypeVar, Union

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.models import Base


ModelType = TypeVar("ModelType", bound=Base)  # type: ignore
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(
        self,
        session: AsyncSession,
        in_obj: CreateSchemaType,
    ) -> ModelType:
        in_obj_data = jsonable_encoder(in_obj)
        db_obj = self.model(**in_obj_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def read(self, session: AsyncSession, id: Any) -> ModelType | None:
        statement = select(self.model).where(self.model.id == id)
        result = await session.execute(statement=statement)
        return result.scalars().first()

    async def read_or_404(self, session: AsyncSession, id: Any) -> ModelType | None:
        db_obj = await self.read(session=session, id=id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__tablename__.capitalize()} not found",
            )
        return db_obj

    async def read_many(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = settings.PAGE_SIZE,
    ) -> list[ModelType]:
        statement = (
            select(self.model).offset(skip).limit(min(limit, settings.PAGE_SIZE))
        )
        result = await session.execute(statement=statement)
        return result.scalars().all()

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        in_obj: Union[UpdateSchemaType, dict[str, Any]],
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(in_obj, dict):
            update_data = in_obj
        else:
            update_data = in_obj.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, id: Any) -> ModelType | None:
        db_obj = await self.read(session=session, id=id)
        await session.delete(db_obj)
        await session.commit()
        return db_obj
