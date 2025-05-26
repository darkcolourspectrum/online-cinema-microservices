from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

# Промежуточная таблица для many-to-many фильмов и жанров
movie_genres = Table(
    'movie_genres',
    Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id'), primary_key=True)
)


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    release_year = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # Длительность в минутах
    
    # Рейтинги
    imdb_rating = Column(Float, nullable=True)
    our_rating = Column(Float, default=0.0)  # Средний рейтинг от пользователей
    
    # Метаданные
    director = Column(String, nullable=True)
    cast = Column(Text, nullable=True)  # Список актеров через запятую
    poster_url = Column(String, nullable=True)  # URL постера
    trailer_url = Column(String, nullable=True)  # URL трейлера
    
    # Для стриминга
    video_url = Column(String, nullable=True)  # URL видеофайла
    is_available = Column(Boolean, default=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    genres = relationship("Genre", secondary=movie_genres, back_populates="movies")