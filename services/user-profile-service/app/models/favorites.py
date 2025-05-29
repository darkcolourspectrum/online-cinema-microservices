from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class FavoriteMovie(Base):
    __tablename__ = "favorite_movies"

    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с профилем пользователя
    user_email = Column(String, index=True, nullable=False)
    
    # ID фильма из Movie Service
    movie_id = Column(Integer, nullable=False)
    
    # Метаданные (для кэширования и быстрого доступа)
    movie_title = Column(String, nullable=True)  # Название фильма (кэш)
    movie_poster_url = Column(String, nullable=True)  # Постер (кэш)
    
    # Временные метки
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Уникальность: один пользователь может добавить фильм в избранное только один раз
    __table_args__ = (
        UniqueConstraint('user_email', 'movie_id', name='_user_movie_favorite'),
    )


class WatchLater(Base):
    __tablename__ = "watch_later"

    id = Column(Integer, primary_key=True, index=True)
    
    user_email = Column(String, index=True, nullable=False)
    
    movie_id = Column(Integer, nullable=False)
    
    movie_title = Column(String, nullable=True)
    movie_poster_url = Column(String, nullable=True)
    
    priority = Column(Integer, default=0)
    
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_email', 'movie_id', name='_user_movie_watch_later'),
    )