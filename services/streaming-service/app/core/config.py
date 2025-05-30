from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql://streaming_user:streaming_password@localhost:5432/streaming_db"
    
    service_name: str = "streaming-service"
    service_port: int = 8005
    debug: bool = False
    
    auth_service_url: str = "http://localhost:8001"
    movie_service_url: str = "http://localhost:8002"
    
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    
    storage_path: str = "/app/storage"
    max_file_size_mb: int = 500
    allowed_video_formats: str = "mp4,avi,mkv,mov,wmv,flv,webm"
    allowed_image_formats: str = "jpg,jpeg,png,webp"
    
    default_video_quality: str = "720p"
    supported_qualities: str = "480p,720p,1080p"
    thumbnail_width: int = 320
    thumbnail_height: int = 180
    
    @property
    def allowed_video_formats_list(self) -> List[str]:
        return [fmt.strip().lower() for fmt in self.allowed_video_formats.split(',')]
    
    @property
    def allowed_image_formats_list(self) -> List[str]:
        return [fmt.strip().lower() for fmt in self.allowed_image_formats.split(',')]
    
    @property
    def supported_qualities_list(self) -> List[str]:
        return [q.strip() for q in self.supported_qualities.split(',')]
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_ignore_empty = True


settings = Settings()