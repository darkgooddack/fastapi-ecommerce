from fastapi import HTTPException
from app.routers.auth import redis_client

def get_user_id_from_redis(token: str):
    username = redis_client.get(token)  # Получаем username из Redis по токену
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return username.decode('utf-8')  # Возвращаем строку, если username найден в Redis