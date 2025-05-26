from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Service
    service_name: str = "auth-service"
    service_port: int = 8001
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()