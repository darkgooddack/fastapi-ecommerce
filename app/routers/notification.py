import json

import jwt
import pika
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from starlette import status

from app.core.config import settings
from app.crud.user import get_user_by_username
from app.crud.notification import get_user_id_from_redis
from app.models import User
from app.models.base import get_db
from app.models.notification import Notification, user_notifications
from app.routers.auth import oauth2_scheme
from app.schemas.notification import NotificationCreate, NotificationOut
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_rabbitmq_connection():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        logging.info(f"✅ Подключение к RabbitMQ успешно!")
        return connection
    except Exception as e:
        logging.error(f"❌ Ошибка подключения к RabbitMQ: {e}")
        return None

@router.post("/send_notifications", summary="Отправка уведомлений пользователям")
async def send_notifications(notification: NotificationCreate, db: Session = Depends(get_db)):
    """
    **Отправка уведомлений пользователям**
    - Создаёт уведомление в БД.
    - Отправляет сообщение через RabbitMQ для дальнейшей обработки.
    """
    # Создаём уведомление в БД
    db_notification = Notification(title=notification.title, message=notification.message)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    # Создаём подключение к RabbitMQ
    connection = get_rabbitmq_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Ошибка подключения к RabbitMQ")

    channel = connection.channel()
    channel.queue_declare(queue="notification_tasks")

    # Формируем сообщение для отправки в очередь
    message = {
        "notification_id": db_notification.id,
        "title": notification.title,
        "message": notification.message,
    }

    # Отправляем сообщение в очередь для обработки
    channel.basic_publish(exchange="", routing_key="notification_tasks", body=json.dumps(message))
    logging.info(f"✅ Задача по отправке уведомления добавлена в очередь RabbitMQ")

    connection.close()

    return {"message": "Уведомление поставлено в очередь для отправки"}


@router.post("/notifications", response_model=list[NotificationOut])
async def get_user_notifications(
    token: str = Depends(oauth2_scheme),  # Получаем токен из заголовка Authorization
    db: Session = Depends(get_db),     # Подключение к базе данных
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")

        if not username:
            raise HTTPException(status_code=400, detail="Invalid token")

        user = db.query(User).filter(User.username == username).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Получаем уведомления для пользователя из промежуточной таблицы
        notifications = db.query(Notification).join(
            user_notifications, user_notifications.c.notification_id == Notification.id
        ).filter(user_notifications.c.user_id == user.id).all()

        if not notifications:
            raise HTTPException(status_code=404, detail="No notifications found for this user")

        return notifications

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/toggle-notifications")
async def toggle_notifications(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    username = payload.get("sub")

    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    db_user = db.query(User).filter(User.username == username).first()

    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.receive_notifications = not db_user.receive_notifications
    db.commit()
    db.refresh(db_user)
    logging.info(f"✅ Переключатель сработал на {db_user.receive_notifications} для пользователя {username}!")
    return {"receive_notifications": db_user.receive_notifications}