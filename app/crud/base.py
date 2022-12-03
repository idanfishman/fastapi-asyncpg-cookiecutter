"""
Defines base class with generic logic for CRUD operations.
Every model should inherit this logic and enrich/override it if needed.

Notice: the CRUD functions DOES NOT validate the given input, therefore you 
should validate the args before passing them to the CRUD functions.
"""

from typing import Any, Generic, Type, TypeVar, Union

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi_pagination.bases import AbstractPage, AbstractParams
from fastapi_pagination.ext.async_sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.models import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    async def create(
        self,
        session: AsyncSession,
        in_obj: CreateSchemaType,
        **attrs,
    ) -> ModelType:
        in_obj_data = jsonable_encoder(in_obj)
        attrs_data = jsonable_encoder(attrs)
        db_obj = self.model(**in_obj_data, **attrs_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def read(self, session: AsyncSession, **attrs) -> ModelType | None:
        statement = select(self.model).filter_by(**attrs)
        result = await session.execute(statement=statement)
        return result.scalars().first()

    async def read_or_404(self, session: AsyncSession, **attrs) -> ModelType:
        db_obj = await self.read(session=session, **attrs)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__tablename__.capitalize()} not found",
            )
        return db_obj

    async def read_many(
        self,
        session: AsyncSession,
        pagination_params: AbstractParams | None = None,
        order_by: str | None = None,
        **attrs,
    ) -> AbstractPage[ModelType]:
        statement = select(self.model).filter_by(**attrs).order_by(order_by)
        result = await paginate(session, statement, pagination_params)
        return result

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

    async def delete(self, session: AsyncSession, db_obj: ModelType) -> ModelType | None:
        await session.delete(db_obj)
        await session.commit()
        return db_obj

    def parse_integrity_error(self, error: IntegrityError) -> dict[str, Any]:
        if not self.model.unique_keys:
            raise NotImplementedError("the model must implement the `unique_keys` property.")

        if error.orig.pgcode == "23505":  # UniqueViolationError
            error_args_str = "".join(error.orig.args)
            for key in self.model.unique_keys:
                if error_args_str.find(key) != -1:
                    return {
                        "loc": ["body", key],
                        "msg": "value already exists",
                    }
        raise error
