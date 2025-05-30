from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class WatchSessionBase(BaseModel):
    movie_id: int
    video_file_id: int
    current_time: float = 0.0
    quality: Optional[str] = None
    volume: float = Field(1.0, ge=0.0, le=1.0)
    playback_speed: float = Field(1.0, ge=0.1, le=3.0)


class WatchSessionCreate(WatchSessionBase):
    pass


class WatchSessionUpdate(BaseModel):
    current_time: Optional[float] = None
    quality: Optional[str] = None
    volume: Optional[float] = Field(None, ge=0.0, le=1.0)
    playback_speed: Optional[float] = Field(None, ge=0.1, le=3.0)
    is_paused: Optional[bool] = None


class WatchSession(WatchSessionBase):
    id: int
    user_email: str
    duration: Optional[float]
    progress_percentage: float
    is_active: bool
    is_completed: bool
    is_paused: bool
    user_agent: Optional[str]
    ip_address: Optional[str]
    device_type: Optional[str]
    started_at: datetime
    last_updated: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class WatchHistoryBase(BaseModel):
    movie_id: int
    total_watch_time: float = 0.0
    completion_percentage: float = 0.0
    watch_count: int = 1
    last_position: float = 0.0
    last_quality: Optional[str] = None
    user_rating: Optional[float] = Field(None, ge=1.0, le=10.0)


class WatchHistory(WatchHistoryBase):
    id: int
    user_email: str
    first_watched: datetime
    last_watched: Optional[datetime]
    
    class Config:
        from_attributes = True


class StreamingStatsBase(BaseModel):
    movie_id: int
    total_views: int = 0
    unique_viewers: int = 0
    completed_views: int = 0
    total_watch_time: float = 0.0
    average_completion_rate: float = 0.0
    average_session_duration: float = 0.0
    most_popular_quality: Optional[str] = None
    average_rating: Optional[float] = None
    total_ratings: int = 0


class StreamingStats(StreamingStatsBase):
    id: int
    quality_distribution: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PlaybackSettings(BaseModel):
    """Настройки воспроизведения"""
    quality: str = "auto"
    volume: float = Field(1.0, ge=0.0, le=1.0)
    playback_speed: float = Field(1.0, ge=0.1, le=3.0)
    autoplay: bool = False
    subtitles_enabled: bool = False
    subtitles_language: Optional[str] = None


class StreamingInfo(BaseModel):
    """Информация для стриминга"""
    video_id: int
    movie_id: int
    stream_urls: Dict[str, str]  # quality -> url
    thumbnail_url: Optional[str]
    duration: Optional[float]
    current_position: float = 0.0
    available_qualities: List[str]
    recommended_quality: str
    subtitles_available: bool = False
    subtitles_urls: Dict[str, str] = {}  # language -> url


class StreamingSessionInfo(BaseModel):
    """Информация о сессии стриминга"""
    session_id: int
    movie_id: int
    video_id: int
    user_email: str
    current_time: float
    duration: Optional[float]
    progress_percentage: float
    quality: Optional[str]
    is_active: bool
    is_paused: bool
    device_type: Optional[str]
    started_at: datetime


class UserWatchStats(BaseModel):
    """Статистика просмотров пользователя"""
    total_movies_watched: int
    total_watch_time: float  # в часах
    favorite_genre: Optional[str]
    average_completion_rate: float
    most_watched_movie: Optional[Dict[str, Any]]
    watch_history: List[WatchHistory] = []


class MovieStreamingStats(BaseModel):
    """Статистика стриминга фильма"""
    movie_id: int
    total_views: int
    unique_viewers: int
    completion_rate: float
    average_rating: Optional[float]
    popular_qualities: List[Dict[str, Any]]  # [{"quality": "1080p", "percentage": 45.2}]
    peak_concurrent_viewers: int
    total_hours_watched: float