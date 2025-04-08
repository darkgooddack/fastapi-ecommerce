from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from .base import AbstractRepository

class UserRepository(AbstractRepository[User]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int):
        result = await self.session.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def list(self):
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def add(self, obj: User):
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, id: int):
        user = await self.get(id)
        if user:
            await self.session.delete(user)

    async def get_by_email(self, email: str) -> User:
        """Проверить, существует ли пользователь с таким email"""
        result = await self.session.execute(
            select(User).filter(User.email == email)
        )
        return result.scalars().first()