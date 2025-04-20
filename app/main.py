from fastapi import FastAPI
from fastapi.responses import RedirectResponse

import logging
import redis
from starlette.middleware.cors import CORSMiddleware

from app.models.base import Base, engine
from app.routers import auth, users, notification

from app.core.config import settings


app = FastAPI(title="Auth API", root_path="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")
app.include_router(notification.router, prefix="/notification")

@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

# Запуск: `uvicorn main:app --reload`
# RabbitMQ: python workers/notification_worker.py