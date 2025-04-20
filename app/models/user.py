from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.notification import user_notifications  # Импортируем связь

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)
    receive_notifications = Column(Boolean, default=True)

    notifications = relationship("Notification", secondary=user_notifications, back_populates="users")
