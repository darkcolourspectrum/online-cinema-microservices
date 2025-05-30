from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.sql import func
from ..core.database import Base


class WatchSession(Base):
    __tablename__ = "watch_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Пользователь и фильм
    user_email = Column(String, nullable=False, index=True)
    movie_id = Column(Integer, nullable=False, index=True)
    video_file_id = Column(Integer, nullable=False, index=True)
    
    # Прогресс просмотра
    current_time = Column(Float, default=0.0)  # Текущая позиция в секундах
    duration = Column(Float, nullable=True)  # Общая длительность
    progress_percentage = Column(Float, default=0.0)  # Прогресс в процентах
    
    # Настройки воспроизведения
    quality = Column(String, nullable=True)  # Выбранное качество
    volume = Column(Float, default=1.0)  # Уровень громкости (0.0 - 1.0)
    playback_speed = Column(Float, default=1.0)  # Скорость воспроизведения
    
    # Статус сессии
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)  # Просмотр завершен
    is_paused = Column(Boolean, default=False)
    
    # Технические данные
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    device_type = Column(String, nullable=True)  # mobile, desktop, tablet, tv
    
    # Временные метки
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    
    user_email = Column(String, nullable=False, index=True)
    movie_id = Column(Integer, nullable=False, index=True)
    
    total_watch_time = Column(Float, default=0.0)  # Общее время просмотра в секундах
    completion_percentage = Column(Float, default=0.0)  # Процент завершения
    watch_count = Column(Integer, default=1)  # Количество просмотров
    
    # Последняя сессия
    last_position = Column(Float, default=0.0)  # Последняя позиция
    last_quality = Column(String, nullable=True)  # Последнее выбранное качество
    
    # Рейтинг и отзыв (опционально)
    user_rating = Column(Float, nullable=True)  # Рейтинг от 1 до 10
    
    # Временные метки
    first_watched = Column(DateTime(timezone=True), server_default=func.now())
    last_watched = Column(DateTime(timezone=True), onupdate=func.now())


class StreamingStats(Base):
    __tablename__ = "streaming_stats"

    id = Column(Integer, primary_key=True, index=True)
    
    movie_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # Счетчики просмотров
    total_views = Column(Integer, default=0)
    unique_viewers = Column(Integer, default=0)
    completed_views = Column(Integer, default=0)  # Просмотры до конца
    
    total_watch_time = Column(Float, default=0.0)  # Общее время просмотра
    average_completion_rate = Column(Float, default=0.0)  # Средний % завершения
    average_session_duration = Column(Float, default=0.0)  # Средняя длительность сессии
    
    most_popular_quality = Column(String, nullable=True)
    quality_distribution = Column(Text, nullable=True)  # JSON со статистикой качества
    
    average_rating = Column(Float, nullable=True)
    total_ratings = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())