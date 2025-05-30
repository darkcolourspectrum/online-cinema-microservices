from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, BigInteger, JSON
from sqlalchemy.sql import func
from ..core.database import Base


class VideoFile(Base):
    __tablename__ = "video_files"

    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с фильмом из Movie Service
    movie_id = Column(Integer, nullable=False, index=True)
    
    # Информация о файле
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Путь к файлу на диске
    file_size = Column(BigInteger, nullable=False)  # Размер в байтах
    mime_type = Column(String, nullable=False)
    
    # Технические характеристики видео
    duration_seconds = Column(Float, nullable=True)  # Длительность в секундах
    resolution_width = Column(Integer, nullable=True)
    resolution_height = Column(Integer, nullable=True)
    quality = Column(String, nullable=True)  # 720p, 1080p и т.д.
    bitrate = Column(Integer, nullable=True)  # Битрейт в kbps
    fps = Column(Float, nullable=True)  # Кадры в секунду
    codec = Column(String, nullable=True)  # Видео кодек
    
    # Превью и миниатюры
    thumbnail_path = Column(String, nullable=True)  # Путь к превью
    preview_path = Column(String, nullable=True)  # Путь к GIF превью
    
    # Статус обработки
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_progress = Column(Float, default=0.0)  # Прогресс обработки (0.0 - 1.0)
    processing_error = Column(Text, nullable=True)  # Ошибка обработки
    
    # Метаданные
    video_metadata = Column(JSON, nullable=True)  # Дополнительные метаданные видео
    
    # Флаги
    is_primary = Column(Boolean, default=False)  # Основной файл для фильма
    is_processed = Column(Boolean, default=False)  # Обработан ли файл
    is_available = Column(Boolean, default=True)  # Доступен ли для стриминга
    
    # Загрузчик
    uploaded_by = Column(String, nullable=False)  # Email пользователя
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


class VideoQuality(Base):
    __tablename__ = "video_qualities"

    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с основным видеофайлом
    original_video_id = Column(Integer, nullable=False, index=True)
    
    # Информация о качестве
    quality = Column(String, nullable=False)  # 480p, 720p, 1080p
    resolution_width = Column(Integer, nullable=False)
    resolution_height = Column(Integer, nullable=False)
    bitrate = Column(Integer, nullable=False)  # Битрейт в kbps
    
    # Путь к файлу
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    
    # Статус
    is_ready = Column(Boolean, default=False)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())