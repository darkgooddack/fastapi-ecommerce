import logging
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.crud.user import create_user, get_user_by_username
from app.schemas.user import UserCreate, UserOut

router = APIRouter()
logging.basicConfig(level=logging.INFO)

@router.post(
    "/register",
    response_model=UserOut,
    summary="Регистрация нового пользователя",
    description="""
    Создает нового пользователя в системе.  
    Если пользователь с таким именем уже существует, возвращает ошибку.  
    Пароль будет зашифрован перед сохранением.
    """,
    responses={
        201: {"description": "Пользователь успешно зарегистрирован"},
        400: {"description": "Пользователь уже существует"}
    },
)
async def register(
        username: str = Form(..., description="Имя пользователя"),
        password: str = Form(..., description="Пароль"),
        db: Session = Depends(get_db)
):
    """
    **Регистрация пользователя**
    - 🔑 Создаёт нового пользователя.
    - ❌ Возвращает ошибку, если пользователь уже зарегистрирован.
    - 🔒 Пароль хранится в зашифрованном виде.
    """

    logging.info(f"✅ Попытка регистрации пользователя: {username}")

    if get_user_by_username(db, username):
        logging.warning(f"❌ Регистрация не удалась: пользователь {username} уже существует")
        raise HTTPException(status_code=400, detail="User already exists")

    # 🔥 Создаем объект UserCreate перед передачей в create_user
    user_data = UserCreate(username=username, password=password)
    new_user = create_user(db, user_data)
    logging.info(f"✅ Пользователь {username} успешно зарегистрирован")

    return new_user
