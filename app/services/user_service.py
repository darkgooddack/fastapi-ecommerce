import logging
import jwt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserOut
from app.core.security import hash_password, verify_password, create_access_token
from datetime import timedelta
from app.core.config import settings
from app.repositories.redis_repository import RedisRepository

class UserService:
    def __init__(self, session: AsyncSession, redis_repo: RedisRepository):
        self.session = session
        self.user_repository = UserRepository(session)
        self.redis_repo = redis_repo

    async def create_user(self, user_create: UserCreate) -> UserOut:

        existing_user = await self.user_repository.get_by_email(user_create.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        hashed_password = hash_password(user_create.password)

        new_user = User(
            email=user_create.email,
            hashed_password=hashed_password
        )

        self.session.add(new_user)

        try:
            await self.session.commit()
            await self.session.refresh(new_user)
        except Exception as e:
            await self.session.rollback()
            raise e

        return UserOut.from_orm(new_user)

    async def authenticate_user(self, email: str, password: str) -> dict:

        user = await self.user_repository.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")


        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        access_token = create_access_token(data={"sub": user.email},
                                           expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

        return {"access_token": access_token, "token_type": "bearer"}

    async def get_user(self, user_id: int) -> UserOut:

        user = await self.user_repository.get(user_id)
        if not user:
            raise ValueError("User not found")
        return UserOut.from_orm(user)

    async def login(self, user_create: UserCreate) -> dict:
        """ Авторизация пользователя и выдача токена """
        logging.info(f"✅ Попытка авторизации для пользователя: {user_create.email}")

        db_user = await self.user_repository.get_by_email(user_create.email)
        if not db_user or not verify_password(user_create.password, db_user.hashed_password):
            logging.error("❌ Неверные учетные данные")
            raise HTTPException(status_code=400, detail="Invalid email or password")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": db_user.email}, expires_delta=access_token_expires)

        await self.redis_repo.save_token(db_user.email, access_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        logging.info(f"✅ Токен выдан пользователю: {db_user.email}")
        return {"access_token": access_token, "token_type": "bearer"}

    async def logout(self, username: str):
        """ Выход пользователя из системы, удаление токена из Redis """
        logging.info(f"✅ Попытка выхода из системы для пользователя: {username}")
        await self.redis_repo.delete_token(username)
        logging.info(f"✅ Пользователь {username} успешно вышел из системы")

    async def protected_route(self, token: str) -> dict:
        """ Проверка токена в Redis """
        logging.info(f"✅ Проверка токена пользователя")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")

        redis_token = await self.redis_repo.get_token(username)
        if redis_token != token:
            logging.error(f"❌ Неверный токен для пользователя {username}")
            raise HTTPException(status_code=401, detail="Invalid token")

        logging.info(f"✅ Доступ разрешён для пользователя {username}")
        return {"message": f"Привет, {username}! Твой токен действителен."}
