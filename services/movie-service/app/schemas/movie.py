from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class GenreBase(BaseModel):
    name: str
    description: Optional[str] = None


class GenreCreate(GenreBase):
    pass


class Genre(GenreBase):
    id: int
    
    class Config:
        from_attributes = True


class MovieBase(BaseModel):
    title: str
    description: Optional[str] = None
    release_year: int
    duration_minutes: int
    director: Optional[str] = None
    cast: Optional[str] = None
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    video_url: Optional[str] = None
    imdb_rating: Optional[float] = None


class MovieCreate(MovieBase):
    genre_ids: List[int] = []  # ID жанров для фильма


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    release_year: Optional[int] = None
    duration_minutes: Optional[int] = None
    director: Optional[str] = None
    cast: Optional[str] = None
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    video_url: Optional[str] = None
    imdb_rating: Optional[float] = None
    genre_ids: Optional[List[int]] = None


class Movie(MovieBase):
    id: int
    our_rating: float
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]
    genres: List[Genre] = []
    
    class Config:
        from_attributes = True


class MovieList(BaseModel):
    movies: List[Movie]
    total: int
    page: int
    per_page: int