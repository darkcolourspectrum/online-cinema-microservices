from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict, Any
import os
import re
from datetime import datetime

from ..core.database import get_db
from ..models.video import VideoFile, VideoQuality
from ..models.watch_session import WatchSession, WatchHistory, StreamingStats
from ..schemas.streaming import (
    WatchSessionCreate, WatchSessionUpdate, WatchSession as WatchSessionSchema,
    StreamingInfo, StreamingSessionInfo, UserWatchStats, MovieStreamingStats
)
from ..utils.auth import get_current_user, get_current_user_optional, get_client_info
from ..utils.file_handler import file_handler
from ..core.config import settings

router = APIRouter(prefix="/stream", tags=["Video Streaming"])


@router.get("/info/{movie_id}", response_model=StreamingInfo)
async def get_streaming_info(
    movie_id: int,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Получить информацию для стриминга фильма"""
    
    # Получаем основной видеофайл для фильма
    video = db.query(VideoFile).filter(
        and_(
            VideoFile.movie_id == movie_id,
            VideoFile.is_available == True,
            VideoFile.is_processed == True
        )
    ).order_by(VideoFile.is_primary.desc(), VideoFile.created_at.desc()).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No available video found for this movie"
        )
    
    # Определяем доступные качества
    available_qualities = settings.supported_qualities_list
    
    # Создаем URLs для разных качеств
    stream_urls = {}
    for quality in available_qualities:
        stream_urls[quality] = f"/api/stream/video/{video.id}?quality={quality}"
    
    # Получаем текущую позицию для авторизованного пользователя
    current_position = 0.0
    if current_user:
        watch_history = db.query(WatchHistory).filter(
            and_(
                WatchHistory.user_email == current_user['email'],
                WatchHistory.movie_id == movie_id
            )
        ).first()
        
        if watch_history:
            current_position = watch_history.last_position
    
    # Рекомендуемое качество (по умолчанию или из истории)
    recommended_quality = settings.default_video_quality
    if current_user:
        last_session = db.query(WatchSession).filter(
            and_(
                WatchSession.user_email == current_user['email'],
                WatchSession.movie_id == movie_id
            )
        ).order_by(WatchSession.last_updated.desc()).first()
        
        if last_session and last_session.quality:
            recommended_quality = last_session.quality
    
    return StreamingInfo(
        video_id=video.id,
        movie_id=movie_id,
        stream_urls=stream_urls,
        thumbnail_url=file_handler.get_file_url(video.thumbnail_path) if video.thumbnail_path else None,
        duration=video.duration_seconds,
        current_position=current_position,
        available_qualities=available_qualities,
        recommended_quality=recommended_quality,
        subtitles_available=False,  # TODO: Implement subtitles
        subtitles_urls={}
    )


@router.get("/video/{video_id}")
async def stream_video(
    video_id: int,
    request: Request,
    quality: str = "720p",
    db: Session = Depends(get_db)
):
    """Стримить видеофайл с поддержкой range requests"""
    
    # Получаем видеофайл
    video = db.query(VideoFile).filter(
        and_(
            VideoFile.id == video_id,
            VideoFile.is_available == True,
            VideoFile.is_processed == True
        )
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found or not available"
        )
    
    # Определяем путь к файлу нужного качества
    video_path = None
    
    # Сначала пытаемся найти конвертированное качество
    quality_video_path = os.path.join(
        settings.storage_path, 'videos', f"video_{video_id}_{quality}.mp4"
    )
    
    if os.path.exists(quality_video_path):
        video_path = quality_video_path
    else:
        # Если нет нужного качества, используем оригинал
        original_path = file_handler.get_full_path(video.file_path)
        if os.path.exists(original_path):
            video_path = original_path
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found on disk"
            )
    
    # Получаем размер файла
    file_size = os.path.getsize(video_path)
    
    # Обрабатываем Range header для HTTP Range Requests
    range_header = request.headers.get('range')
    
    if range_header:
        # Парсим Range header
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            # Ограничиваем диапазон
            start = max(0, start)
            end = min(file_size - 1, end)
            content_length = end - start + 1
            
            def iter_file_range():
                with open(video_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(content_length),
                'Content-Type': 'video/mp4'
            }
            
            return StreamingResponse(
                iter_file_range(),
                status_code=206,
                headers=headers
            )
    
    # Если нет Range header, отдаем весь файл
    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Length': str(file_size),
        'Content-Type': 'video/mp4'
    }
    
    return FileResponse(video_path, headers=headers)


@router.post("/session", response_model=WatchSessionSchema)
async def start_watch_session(
    session_data: WatchSessionCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Начать сессию просмотра"""
    
    # Проверяем существование видео
    video = db.query(VideoFile).filter(VideoFile.id == session_data.video_file_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Получаем информацию о клиенте
    client_info = get_client_info(request)
    
    # Создаем новую сессию или обновляем существующую
    existing_session = db.query(WatchSession).filter(
        and_(
            WatchSession.user_email == current_user['email'],
            WatchSession.movie_id == session_data.movie_id,
            WatchSession.is_active == True
        )
    ).first()
    
    if existing_session:
        # Обновляем существующую сессию
        existing_session.video_file_id = session_data.video_file_id
        existing_session.current_time = session_data.current_time
        existing_session.quality = session_data.quality
        existing_session.volume = session_data.volume
        existing_session.playback_speed = session_data.playback_speed
        existing_session.is_paused = False
        existing_session.last_updated = datetime.utcnow()
        existing_session.user_agent = client_info['user_agent']
        existing_session.ip_address = client_info['ip_address']
        existing_session.device_type = client_info['device_type']
        
        db.commit()
        db.refresh(existing_session)
        return existing_session
    else:
        # Создаем новую сессию
        watch_session = WatchSession(
            user_email=current_user['email'],
            movie_id=session_data.movie_id,
            video_file_id=session_data.video_file_id,
            current_time=session_data.current_time,
            duration=video.duration_seconds,
            quality=session_data.quality,
            volume=session_data.volume,
            playback_speed=session_data.playback_speed,
            user_agent=client_info['user_agent'],
            ip_address=client_info['ip_address'],
            device_type=client_info['device_type']
        )
        
        db.add(watch_session)
        db.commit()
        db.refresh(watch_session)
        return watch_session


@router.put("/session/{session_id}", response_model=WatchSessionSchema)
async def update_watch_session(
    session_id: int,
    session_update: WatchSessionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить сессию просмотра"""
    
    session = db.query(WatchSession).filter(
        and_(
            WatchSession.id == session_id,
            WatchSession.user_email == current_user['email']
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch session not found"
        )
    
    # Обновляем поля
    update_data = session_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    # Вычисляем прогресс
    if session.duration and session.current_time:
        session.progress_percentage = min(100.0, (session.current_time / session.duration) * 100)
    
    # Проверяем завершение просмотра
    if session.progress_percentage >= 90.0:  # Считаем завершенным при 90%
        session.is_completed = True
        session.completed_at = datetime.utcnow()
    
    session.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    # Обновляем историю просмотров
    await _update_watch_history(current_user['email'], session.movie_id, session, db)
    
    return session


@router.post("/session/{session_id}/end")
async def end_watch_session(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Завершить сессию просмотра"""
    
    session = db.query(WatchSession).filter(
        and_(
            WatchSession.id == session_id,
            WatchSession.user_email == current_user['email']
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch session not found"
        )
    
    # Завершаем сессию
    session.is_active = False
    session.last_updated = datetime.utcnow()
    
    # Обновляем историю просмотров
    await _update_watch_history(current_user['email'], session.movie_id, session, db)
    
    # Обновляем общую статистику
    await _update_streaming_stats(session.movie_id, session, db)
    
    db.commit()
    
    return {"message": "Watch session ended"}


@router.get("/sessions/active", response_model=list[StreamingSessionInfo])
async def get_active_sessions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить активные сессии просмотра пользователя"""
    
    sessions = db.query(WatchSession).filter(
        and_(
            WatchSession.user_email == current_user['email'],
            WatchSession.is_active == True
        )
    ).order_by(WatchSession.last_updated.desc()).all()
    
    return [
        StreamingSessionInfo(
            session_id=session.id,
            movie_id=session.movie_id,
            video_id=session.video_file_id,
            user_email=session.user_email,
            current_time=session.current_time,
            duration=session.duration,
            progress_percentage=session.progress_percentage,
            quality=session.quality,
            is_active=session.is_active,
            is_paused=session.is_paused,
            device_type=session.device_type,
            started_at=session.started_at
        )
        for session in sessions
    ]


@router.get("/stats/user", response_model=UserWatchStats)
async def get_user_watch_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику просмотров пользователя"""
    
    # Получаем общую статистику
    total_movies = db.query(WatchHistory).filter(
        WatchHistory.user_email == current_user['email']
    ).count()
    
    total_time_result = db.query(func.sum(WatchHistory.total_watch_time)).filter(
        WatchHistory.user_email == current_user['email']
    ).scalar()
    
    total_watch_time = (total_time_result or 0) / 3600  # Конвертируем в часы
    
    avg_completion = db.query(func.avg(WatchHistory.completion_percentage)).filter(
        WatchHistory.user_email == current_user['email']
    ).scalar() or 0
    
    # Получаем историю просмотров
    watch_history = db.query(WatchHistory).filter(
        WatchHistory.user_email == current_user['email']
    ).order_by(WatchHistory.last_watched.desc()).limit(10).all()
    
    return UserWatchStats(
        total_movies_watched=total_movies,
        total_watch_time=round(total_watch_time, 2),
        favorite_genre=None,  # TODO: Implement based on movie genres
        average_completion_rate=round(avg_completion, 2),
        most_watched_movie=None,  # TODO: Implement
        watch_history=watch_history
    )


@router.get("/stats/movie/{movie_id}", response_model=MovieStreamingStats)
async def get_movie_streaming_stats(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Получить статистику стриминга фильма"""
    
    # Получаем статистику из базы
    stats = db.query(StreamingStats).filter(StreamingStats.movie_id == movie_id).first()
    
    if not stats:
        # Если статистики нет, создаем пустую
        return MovieStreamingStats(
            movie_id=movie_id,
            total_views=0,
            unique_viewers=0,
            completion_rate=0.0,
            average_rating=None,
            popular_qualities=[],
            peak_concurrent_viewers=0,
            total_hours_watched=0.0
        )
    
    # Парсим распределение качеств
    popular_qualities = []
    if stats.quality_distribution:
        # TODO: Parse JSON quality distribution
        pass
    
    return MovieStreamingStats(
        movie_id=movie_id,
        total_views=stats.total_views,
        unique_viewers=stats.unique_viewers,
        completion_rate=stats.average_completion_rate,
        average_rating=stats.average_rating,
        popular_qualities=popular_qualities,
        peak_concurrent_viewers=0,  # TODO: Implement real-time tracking
        total_hours_watched=round(stats.total_watch_time / 3600, 2)
    )


async def _update_watch_history(user_email: str, movie_id: int, session: WatchSession, db: Session):
    """Обновить историю просмотров"""
    
    history = db.query(WatchHistory).filter(
        and_(
            WatchHistory.user_email == user_email,
            WatchHistory.movie_id == movie_id
        )
    ).first()
    
    if history:
        # Обновляем существующую запись
        history.total_watch_time += (session.current_time - (history.last_position or 0))
        history.completion_percentage = max(history.completion_percentage, session.progress_percentage)
        history.last_position = session.current_time
        history.last_quality = session.quality
        history.last_watched = datetime.utcnow()
        
        if session.is_completed:
            history.watch_count += 1
    else:
        # Создаем новую запись
        history = WatchHistory(
            user_email=user_email,
            movie_id=movie_id,
            total_watch_time=session.current_time,
            completion_percentage=session.progress_percentage,
            last_position=session.current_time,
            last_quality=session.quality,
            watch_count=1 if session.is_completed else 0
        )
        db.add(history)


async def _update_streaming_stats(movie_id: int, session: WatchSession, db: Session):
    """Обновить общую статистику стриминга"""
    
    stats = db.query(StreamingStats).filter(StreamingStats.movie_id == movie_id).first()
    
    if not stats:
        # Создаем новую статистику
        stats = StreamingStats(movie_id=movie_id)
        db.add(stats)
    
    # Обновляем счетчики
    stats.total_views += 1
    if session.is_completed:
        stats.completed_views += 1
    
    # Обновляем время просмотра
    stats.total_watch_time += session.current_time
    
    # Пересчитываем средние значения
    if stats.total_views > 0:
        stats.average_completion_rate = (stats.completed_views / stats.total_views) * 100
        stats.average_session_duration = stats.total_watch_time / stats.total_views
    
    # TODO: Обновить unique_viewers (требует отслеживание уникальных пользователей)
    # TODO: Обновить most_popular_quality и quality_distribution