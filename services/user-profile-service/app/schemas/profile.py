from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserProfileBase(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_genres: Optional[List[int]] = None
    language: str = "en"
    notifications_enabled: bool = True


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_genres: Optional[List[int]] = None
    language: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class UserProfile(UserProfileBase):
    id: int
    user_email: str
    movies_watched: int
    total_watch_time: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_active: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProfileStats(BaseModel):
    """Статистика пользователя"""
    movies_watched: int
    total_watch_time: int
    favorite_movies_count: int
    watch_later_count: int
    most_watched_genres: List[dict]  # [{"genre_name": "Action", "count": 5}]
    
    
class UserProfileWithStats(UserProfile):
    """Профиль пользователя с расширенной статистикой"""
    stats: UserProfileStats