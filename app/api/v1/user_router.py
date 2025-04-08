from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserOut
from app.services.user_service import UserService
from sqlalchemy.orm import Session
from app.db.init_db import get_db
from app.core.security import oauth2_scheme
from app.repositories.redis_repository import RedisRepository

router = APIRouter()

def get_redis_repo() -> RedisRepository:
    return RedisRepository()

@router.post("/register", response_model=UserOut, summary="Регистрация нового пользователя")
async def register(user: UserCreate, db: Session = Depends(get_db), redis_repo: RedisRepository = Depends(get_redis_repo)):
    user_service = UserService(db, redis_repo=redis_repo)
    return await user_service.create_user(user)

@router.post("/token", summary="Авторизация пользователя")
async def login(user: UserCreate, db: Session = Depends(get_db), redis_repo: RedisRepository = Depends(get_redis_repo)):
    user_service = UserService(db, redis_repo=redis_repo)
    return await user_service.login(user)

@router.post("/logout", summary="Выход из системы")
async def logout(username: str, db: Session = Depends(get_db), redis_repo: RedisRepository = Depends(get_redis_repo)):
    user_service = UserService(db, redis_repo=redis_repo)
    user_service.logout(username)
    return {"message": "Вы успешно вышли из системы"}

@router.get("/protected", summary="Защищённый маршрут")
async def protected_route(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), redis_repo: RedisRepository = Depends(get_redis_repo)):
    user_service = UserService(db, redis_repo=redis_repo)
    return await user_service.protected_route(token)