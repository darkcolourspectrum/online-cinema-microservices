from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class VideoFileBase(BaseModel):
    movie_id: int
    quality: Optional[str] = None
    is_primary: bool = False


class VideoFileCreate(VideoFileBase):
    pass


class VideoFileUpdate(BaseModel):
    quality: Optional[str] = None
    is_primary: Optional[bool] = None
    is_available: Optional[bool] = None
    processing_status: Optional[str] = None


class VideoFile(VideoFileBase):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    duration_seconds: Optional[float]
    resolution_width: Optional[int]
    resolution_height: Optional[int]
    bitrate: Optional[int]
    fps: Optional[float]
    codec: Optional[str]
    thumbnail_path: Optional[str]
    preview_path: Optional[str]
    processing_status: str
    processing_progress: float
    processing_error: Optional[str]
    video_metadata: Optional[Dict[str, Any]]
    is_processed: bool
    is_available: bool
    uploaded_by: str
    created_at: datetime
    updated_at: Optional[datetime]
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class VideoQualityBase(BaseModel):
    quality: str
    resolution_width: int
    resolution_height: int
    bitrate: int


class VideoQuality(VideoQualityBase):
    id: int
    original_video_id: int
    file_size: int
    is_ready: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoUploadResponse(BaseModel):
    """Ответ при загрузке видео"""
    video_id: int
    message: str
    processing_status: str
    estimated_processing_time: Optional[str] = None


class VideoProcessingStatus(BaseModel):
    """Статус обработки видео"""
    video_id: int
    status: str  # pending, processing, completed, failed
    progress: float  # 0.0 - 1.0
    error_message: Optional[str] = None
    available_qualities: List[str] = []
    thumbnail_url: Optional[str] = None


class VideoListResponse(BaseModel):
    """Список видеофайлов"""
    videos: List[VideoFile]
    total: int
    page: int
    per_page: int


class VideoMetadata(BaseModel):
    """Метаданные видеофайла"""
    duration: Optional[float]
    width: Optional[int]
    height: Optional[int]
    bitrate: Optional[int]
    fps: Optional[float]
    codec: Optional[str]
    audio_codec: Optional[str]
    file_format: Optional[str]
    creation_time: Optional[str]