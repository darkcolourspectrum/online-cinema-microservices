from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..core.database import Base


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # Связь с фильмами (many-to-many через промежуточную таблицу)
    movies = relationship("Movie", secondary="movie_genres", back_populates="genres")