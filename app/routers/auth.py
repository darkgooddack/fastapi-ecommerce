import logging
import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.core.security import verify_password, create_access_token
from app.crud.user import get_user_by_username
from app.schemas.user import UserCreate
from fastapi.security import OAuth2PasswordBearer
import jwt
from redis.exceptions import RedisError
from datetime import timedelta
from app.core.config import settings

try:
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    redis_client.ping()
except RedisError:
    logging.critical("🚨 Ошибка подключения к Redis! Убедитесь, что сервер Redis запущен.")
    redis_client = None  # Отключаем Redis, чтобы код мог работать без него

router = APIRouter()
logging.basicConfig(level=logging.INFO)

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

@router.post("/token", summary="Авторизация пользователя")
async def login(user: UserCreate, db: Session = Depends(get_db)):
    """
    **Авторизация пользователя**
    - 🔑 Проверяет логин и пароль.
    - 🎫 Возвращает JWT-токен для доступа к защищённым API.
    - ❌ Ошибка, если логин или пароль неверные.
    """
    logging.info(f"✅ Запрос авторизации для пользователя: {user.username}")

    db_user = get_user_by_username(db, user.username)

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logging.error("❌ Ошибка: неверные учетные данные!")
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Генерация токена с временем жизни
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)

    # Сохранение токена в Redis, если он доступен
    if redis_client:
        try:
            redis_client.setex(f"token:{db_user.username}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, access_token)
            logging.info(f"✅ Токен пользователя {db_user.username} сохранён в Redis")
        except RedisError:
            logging.error("⚠️ Ошибка при сохранении токена в Redis")

    logging.info(f"✅ Выдан токен пользователю: {db_user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    """
    **Защищённый маршрут**
    - Проверяет токен в Redis.
    - Возвращает сообщение, если токен действителен.
    """
    try:
        # Декодируем токен
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")

        # Проверяем токен в Redis (если Redis доступен)
        if redis_client:
            stored_token = redis_client.get(f"token:{user_id}")
            if stored_token is None:
                logging.error(f"❌ Токен отсутствует в Redis для пользователя {user_id}")
                raise HTTPException(status_code=401, detail="Invalid token")

            if stored_token != token:
                logging.error(f"❌ Токен пользователя {user_id} не совпадает с хранимым в Redis")
                raise HTTPException(status_code=401, detail="Invalid token")

        logging.info(f"✅ Доступ разрешён для пользователя {user_id}")
        return {"message": f"Привет, {user_id}! Твой токен действителен."}

    except jwt.PyJWTError:
        logging.error("❌ Ошибка: токен недействителен")
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """
    **Выход из системы**
    - Удаляет токен из Redis.
    - Пользователь становится разлогиненым.
    """
    try:
        # Декодируем токен
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")

        if redis_client:
            try:
                if redis_client.delete(f"token:{user_id}"):
                    logging.info(f"✅ Пользователь {user_id} вышел из системы, токен удалён из Redis")
                    return {"message": "Вы успешно вышли из системы"}
                else:
                    logging.warning(f"⚠️ Попытка выхода: токен пользователя {user_id} уже отсутствует в Redis")
                    return {"message": "Токен уже недействителен или отсутствует"}
            except RedisError:
                logging.error("⚠️ Ошибка при удалении токена из Redis")

        return {"message": "Вы вышли из системы, но Redis недоступен"}

    except jwt.ExpiredSignatureError:
        logging.warning("⚠️ Попытка выхода с уже истекшим токеном")
        return {"message": "Вы уже вышли из системы (токен истёк)"}