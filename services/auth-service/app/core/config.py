from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://auth_user:auth_password@localhost:5432/auth_db"
    
    # JWT
    jwt_secret_key: str = "r-R1wNVFS1f18q8fSBE0buQ52YftDHK56u3Xz1zkRMo="
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Service
    service_name: str = "auth-service"
    service_port: int = 8001
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_ignore_empty = True


settings = Settings()