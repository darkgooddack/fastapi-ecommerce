from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

# Промежуточная таблица для связи User <-> Notification
user_notifications = Table(
    "user_notifications",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("notification_id", Integer, ForeignKey("notifications.id"), primary_key=True),
)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    message = Column(String)
    created_at = Column(DateTime, default=func.now())

    users = relationship("User", secondary=user_notifications, back_populates="notifications")
