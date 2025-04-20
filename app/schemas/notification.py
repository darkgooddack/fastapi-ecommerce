from datetime import datetime

from pydantic import BaseModel

class NotificationCreate(BaseModel):
    title: str
    message: str

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True