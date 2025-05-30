from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
import httpx

from ..core.database import get_db
from ..models.video import VideoFile
from ..schemas.video import VideoUploadResponse, VideoProcessingStatus, VideoFile as VideoFileSchema
from ..utils.auth import get_current_user
from ..utils.file_handler import file_handler
from ..utils.video_processor import video_processor
from ..core.config import settings

router = APIRouter(prefix="/upload", tags=["Video Upload"])

# Словарь для отслеживания процессов обработки видео
processing_tasks = {}


async def update_video_processing_status(video_id: int, status: str, progress: float, db_session=None):
    """Callback для обновления статуса обработки видео"""
    if db_session:
        video = db_session.query(VideoFile).filter(VideoFile.id == video_id).first()
        if video:
            video.processing_status = status
            video.processing_progress = progress
            if status == 'completed':
                video.is_processed = True
            elif status == 'failed':
                video.is_processed = False
            db_session.commit()


async def process_uploaded_video(video_id: int, file_path: str):
    """Фоновая задача для обработки загруженного видео"""
    from ..core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Обновляем статус на "processing"
        await update_video_processing_status(video_id, 'processing', 0.0, db)
        
        # Получаем информацию о видео
        video_info = await video_processor.get_video_info(file_path)
        
        # Обновляем метаданные видео в базе
        video = db.query(VideoFile).filter(VideoFile.id == video_id).first()
        if video:
            video.duration_seconds = video_info.get('duration')
            video.resolution_width = video_info.get('width')
            video.resolution_height = video_info.get('height')
            video.bitrate = video_info.get('bitrate')
            video.fps = video_info.get('fps')
            video.codec = video_info.get('codec')
            video.video_metadata = video_info
            db.commit()
        
        # Создаем callback для обновления прогресса
        async def progress_callback(vid_id: int, stat: str, prog: float):
            await update_video_processing_status(vid_id, stat, prog, db)
        
        # Запускаем обработку видео
        result = await video_processor.process_video_async(video_id, file_path, progress_callback)
        
        # Обновляем финальный статус
        if result['status'] == 'completed':
            if video:
                video.processing_status = 'completed'
                video.processing_progress = 1.0
                video.is_processed = True
                
                # Сохраняем пути к созданным файлам
                if result.get('thumbnail_created'):
                    video.thumbnail_path = result.get('thumbnail_path')
                if result.get('preview_created'):
                    video.preview_path = result.get('preview_path')
                
                db.commit()
        else:
            if video:
                video.processing_status = 'failed'
                video.processing_error = '; '.join(result.get('errors', []))
                db.commit()
    
    except Exception as e:
        # В случае ошибки обновляем статус
        await update_video_processing_status(video_id, 'failed', 1.0, db)
        video = db.query(VideoFile).filter(VideoFile.id == video_id).first()
        if video:
            video.processing_error = str(e)
            db.commit()
    
    finally:
        db.close()
        # Удаляем задачу из отслеживания
        if video_id in processing_tasks:
            del processing_tasks[video_id]


@router.post("/video", response_model=VideoUploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    movie_id: int = Form(...),
    file: UploadFile = File(...),
    quality: Optional[str] = Form(None),
    is_primary: bool = Form(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Загрузка видеофайла для фильма"""
    
    # Проверяем, существует ли фильм
    async with httpx.AsyncClient() as client:
        try:
            movie_response = await client.get(f"{settings.movie_service_url}/movies/{movie_id}")
            if movie_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not found"
                )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Movie service unavailable"
            )
    
    # Сохраняем файл
    try:
        full_path, relative_path, file_info = await file_handler.save_video_file(file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Создаем запись в базе данных
    video_file = VideoFile(
        movie_id=movie_id,
        filename=file_info['filename'],
        original_filename=file_info['original_filename'],
        file_path=relative_path,
        file_size=file_info['file_size'],
        mime_type=file_info['mime_type'],
        quality=quality,
        is_primary=is_primary,
        uploaded_by=current_user['email'],
        processing_status='pending'
    )
    
    db.add(video_file)
    db.commit()
    db.refresh(video_file)
    
    # Запускаем обработку видео в фоне
    processing_tasks[video_file.id] = True
    background_tasks.add_task(process_uploaded_video, video_file.id, full_path)
    
    return VideoUploadResponse(
        video_id=video_file.id,
        message="Video uploaded successfully and processing started",
        processing_status="pending",
        estimated_processing_time="5-15 minutes"
    )


@router.get("/status/{video_id}", response_model=VideoProcessingStatus)
async def get_processing_status(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Получить статус обработки видео"""
    
    video = db.query(VideoFile).filter(VideoFile.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Определяем доступные качества
    available_qualities = []
    if video.is_processed and video.processing_status == 'completed':
        # Получаем список созданных качеств (это может быть реализовано через VideoQuality модель)
        available_qualities = settings.supported_qualities_list
    
    return VideoProcessingStatus(
        video_id=video.id,
        status=video.processing_status,
        progress=video.processing_progress,
        error_message=video.processing_error,
        available_qualities=available_qualities,
        thumbnail_url=file_handler.get_file_url(video.thumbnail_path) if video.thumbnail_path else None
    )


@router.get("/videos", response_model=list[VideoFileSchema])
async def get_uploaded_videos(
    movie_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить список загруженных видео"""
    
    query = db.query(VideoFile).filter(VideoFile.uploaded_by == current_user['email'])
    
    if movie_id:
        query = query.filter(VideoFile.movie_id == movie_id)
    
    videos = query.order_by(VideoFile.created_at.desc()).all()
    return videos


@router.delete("/video/{video_id}")
async def delete_video(
    video_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить видеофайл"""
    
    video = db.query(VideoFile).filter(VideoFile.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Проверяем права доступа
    if video.uploaded_by != current_user['email']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own videos"
        )
    
    # Удаляем файлы
    files_to_delete = [video.file_path]
    if video.thumbnail_path:
        files_to_delete.append(video.thumbnail_path)
    if video.preview_path:
        files_to_delete.append(video.preview_path)
    
    for file_path in files_to_delete:
        file_handler.delete_file(file_path)
    
    # Удаляем запись из базы
    db.delete(video)
    db.commit()
    
    return {"message": "Video deleted successfully"}


@router.post("/retry-processing/{video_id}")
async def retry_video_processing(
    video_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Повторить обработку видео"""
    
    video = db.query(VideoFile).filter(VideoFile.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Проверяем права доступа
    if video.uploaded_by != current_user['email']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only retry processing for your own videos"
        )
    
    # Проверяем, что видео в состоянии failed
    if video.processing_status not in ['failed', 'pending']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video processing can only be retried for failed or pending videos"
        )
    
    # Сбрасываем статус
    video.processing_status = 'pending'
    video.processing_progress = 0.0
    video.processing_error = None
    video.is_processed = False
    db.commit()
    
    # Запускаем обработку заново
    full_path = file_handler.get_full_path(video.file_path)
    processing_tasks[video.id] = True
    background_tasks.add_task(process_uploaded_video, video.id, full_path)
    
    return {"message": "Video processing restarted"}


@router.get("/cleanup-temp")
async def cleanup_temp_files(
    current_user: dict = Depends(get_current_user)
):
    """Очистка временных файлов (только для авторизованных пользователей)"""
    await file_handler.cleanup_temp_files()
    return {"message": "Temporary files cleaned up"}