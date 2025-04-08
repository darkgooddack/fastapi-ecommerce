from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    DATABASE_URL: str
    SQLALCHEMY_DATABASE_URL: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()