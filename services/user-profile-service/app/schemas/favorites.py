from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class FavoriteMovieBase(BaseModel):
    movie_id: int


class FavoriteMovieCreate(FavoriteMovieBase):
    pass


class FavoriteMovie(FavoriteMovieBase):
    id: int
    user_email: str
    movie_title: Optional[str]
    movie_poster_url: Optional[str]
    added_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteMovieWithDetails(FavoriteMovie):
    """Избранный фильм с полной информацией из Movie Service"""
    movie_details: Optional[Dict[Any, Any]] = None


class WatchLaterBase(BaseModel):
    movie_id: int
    priority: int = 0


class WatchLaterCreate(WatchLaterBase):
    pass


class WatchLaterUpdate(BaseModel):
    priority: Optional[int] = None


class WatchLater(WatchLaterBase):
    id: int
    user_email: str
    movie_title: Optional[str]
    movie_poster_url: Optional[str]
    added_at: datetime
    
    class Config:
        from_attributes = True


class WatchLaterWithDetails(WatchLater):
    """Фильм из списка "посмотреть позже" с полной информацией"""
    movie_details: Optional[Dict[Any, Any]] = None


class FavoritesList(BaseModel):
    """Список избранных фильмов"""
    favorites: List[FavoriteMovieWithDetails]
    total: int


class WatchLaterList(BaseModel):
    """Список фильмов "посмотреть позже" """
    watch_later: List[WatchLaterWithDetails]
    total: int