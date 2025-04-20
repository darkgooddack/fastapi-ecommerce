import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pika
import logging
from app.models.user import User
from app.models.notification import Notification, user_notifications
from sqlalchemy.orm import Session
from app.models.base import get_db, SessionLocal

def process_notification(message, db: Session):
    # Получаем уведомление из базы по ID
    notification = db.query(Notification).filter(Notification.id == message['notification_id']).first()

    if not notification:
        logging.error(f"❌ Уведомление с ID {message['notification_id']} не найдено")
        return

    # Получаем пользователей, которые подписаны на уведомления
    users = db.query(User).filter(User.receive_notifications == True).all()

    if not users:
        logging.info("⚠️ Нет пользователей с активными уведомлениями.")
        return

    # Отправка уведомлений пользователям
    for user in users:
        logging.info(
            f"📩 Отправляем уведомление пользователю {user.username} ({user.email}): {notification.title} - {notification.message}")

        # Добавляем связь между пользователем и уведомлением
        user_notification = user_notifications.insert().values(user_id=user.id, notification_id=notification.id)
        db.execute(user_notification)
        db.commit()
        logging.info(f"✅ Связь пользователя {user.username} с уведомлением добавлена в таблицу")


def callback(ch, method, properties, body):
    message = json.loads(body)
    logging.info(f"📩 Получено уведомление для обработки: {message}")

    # Создаём сессию для работы с базой данных
    db = SessionLocal()

    try:
        process_notification(message, db)
    except Exception as e:
        logging.error(f"❌ Ошибка при обработке уведомления: {e}")
    finally:
        db.close()  # Закрываем сессию после обработки


# Подключение к RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()

# Декларация очереди
channel.queue_declare(queue="notification_tasks")

# Подписка на очередь
channel.basic_consume(queue="notification_tasks", on_message_callback=callback, auto_ack=True)

logging.info("🎧 Ожидание уведомлений для обработки...")
channel.start_consuming()
