from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings

# Создание асинхронного движка
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, echo=True)

# Создание асинхронной сессии
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()

# Асинхронная функция для получения сессии
async def get_db():
    async with async_session() as session:
        yield session
