import redis
from app.core.config import settings
from redis.exceptions import RedisError
import logging

# Создание клиента Redis
class RedisRepository:
    def __init__(self):
        try:
            self.client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
            self.client.ping()  # Проверка соединения с Redis
        except RedisError as e:
            logging.critical(f"🚨 Ошибка подключения к Redis: {e}")
            self.client = None

    def save_token(self, username: str, token: str, expire_seconds: int):
        """ Сохранение токена в Redis с истечением срока действия. """
        if self.client:
            try:
                self.client.setex(f"token:{username}", expire_seconds, token)
                logging.info(f"✅ Токен пользователя {username} сохранён в Redis")
            except RedisError:
                logging.error(f"⚠️ Ошибка при сохранении токена в Redis для пользователя {username}")

    def get_token(self, username: str) -> str:
        """ Получение токена пользователя из Redis. """
        if self.client:
            try:
                return self.client.get(f"token:{username}")
            except RedisError:
                logging.error(f"⚠️ Ошибка при получении токена для пользователя {username} из Redis")
        return None

    def delete_token(self, username: str):
        """ Удаление токена из Redis. """
        if self.client:
            try:
                if self.client.delete(f"token:{username}"):
                    logging.info(f"✅ Токен пользователя {username} удалён из Redis")
                else:
                    logging.warning(f"⚠️ Попытка удаления токена для {username}, токен не найден")
            except RedisError:
                logging.error(f"⚠️ Ошибка при удалении токена для пользователя {username} из Redis")
