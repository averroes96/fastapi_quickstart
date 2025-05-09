__all__ = ("users_service",)
import uuid
from typing import TYPE_CHECKING

from core.db.repositories import BaseRepository
from core.helpers import to_db_encoder
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from domain.authorization.tables import Group, Permission, Role
from domain.users.enums import UserStatuses
from domain.users.schemas.requests import UserCreateSchema
from domain.users.tables import User

if TYPE_CHECKING:
    from sqlalchemy.engine import ChunkedIteratorResult, CursorResult


class UsersService(BaseRepository):
    async def create(self, *, session: AsyncSession, obj: UserCreateSchema) -> User:
        obj.status = UserStatuses.CONFIRMED  # Automatically activates User!!!
        async with session.begin_nested():
            statement = insert(self.model).values(**to_db_encoder(obj=obj)).returning(self.model)
            result: CursorResult = await session.execute(statement=statement)
            return result.scalar_one()
            # return await self.get_with_grp(session=session, id=result.inserted_primary_key[0])

    async def get_with_grp(self, *, session: AsyncSession, id: uuid.UUID) -> User | None:
        statement = (
            select(self.model)
            .where(self.model.id == id)
            .where(self.model.status.in_((UserStatuses.CONFIRMED, UserStatuses.FORCE_CHANGE_PASSWORD)))
            .join(Group, isouter=True)
            .join(Role, isouter=True)
            .join(Permission, isouter=True)
            .options(contains_eager(User.groups), contains_eager(User.roles), contains_eager(User.permissions))
        )
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, *, session: AsyncSession, email: str) -> User | None:
        statement = select(self.model).where(self.model.email == email)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        return result.scalar_one_or_none()


users_service = UsersService(model=User)
