from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://movie_user:movie_password@localhost:5432/movie_db"
    
    # Service
    service_name: str = "movie-service"
    service_port: int = 8002
    debug: bool = False
    
    # Auth Service
    auth_service_url: str = "http://localhost:8001"
    
    # JWT 
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_ignore_empty = True


settings = Settings()