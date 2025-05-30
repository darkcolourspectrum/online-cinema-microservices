import os
import uuid
import aiofiles
from typing import Optional, BinaryIO
from fastapi import UploadFile, HTTPException, status
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """Класс для работы с файлами"""
    
    def __init__(self):
        self.storage_path = settings.storage_path
        self.max_file_size = settings.max_file_size_bytes
        self.allowed_video_formats = settings.allowed_video_formats_list
        self.allowed_image_formats = settings.allowed_image_formats_list
        
        # Создаем необходимые директории
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Создает необходимые директории для хранения файлов"""
        directories = [
            os.path.join(self.storage_path, 'videos'),
            os.path.join(self.storage_path, 'thumbnails'),
            os.path.join(self.storage_path, 'temp'),
            os.path.join(self.storage_path, 'uploads')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def validate_video_file(self, file: UploadFile) -> bool:
        """Валидирует видеофайл"""
        # Проверяем размер файла
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
            )
        
        # Проверяем расширение файла
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in self.allowed_video_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File format '{file_extension}' is not supported. Allowed formats: {', '.join(self.allowed_video_formats)}"
            )
        
        # Проверяем MIME type
        if file.content_type and not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a video file"
            )
        
        return True
    
    def validate_image_file(self, file: UploadFile) -> bool:
        """Валидирует изображение"""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in self.allowed_image_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image format '{file_extension}' is not supported. Allowed formats: {', '.join(self.allowed_image_formats)}"
            )
        
        if file.content_type and not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image file"
            )
        
        return True
    
    def generate_unique_filename(self, original_filename: str, prefix: str = "") -> str:
        """Генерирует уникальное имя файла"""
        file_extension = original_filename.split('.')[-1].lower()
        unique_id = str(uuid.uuid4())
        
        if prefix:
            return f"{prefix}_{unique_id}.{file_extension}"
        else:
            return f"{unique_id}.{file_extension}"
    
    async def save_upload_file(self, file: UploadFile, subdirectory: str = "uploads") -> tuple[str, str]:
        """
        Сохраняет загруженный файл
        Возвращает: (full_path, relative_path)
        """
        # Генерируем уникальное имя файла
        unique_filename = self.generate_unique_filename(file.filename)
        
        # Создаем полный путь
        save_directory = os.path.join(self.storage_path, subdirectory)
        os.makedirs(save_directory, exist_ok=True)
        
        full_path = os.path.join(save_directory, unique_filename)
        relative_path = os.path.join(subdirectory, unique_filename)
        
        try:
            # Сохраняем файл
            async with aiofiles.open(full_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Получаем размер файла
            file_size = os.path.getsize(full_path)
            
            logger.info(f"File saved: {full_path} ({file_size} bytes)")
            
            return full_path, relative_path
            
        except Exception as e:
            # Удаляем файл если произошла ошибка
            if os.path.exists(full_path):
                os.remove(full_path)
            
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error saving file"
            )
    
    async def save_video_file(self, file: UploadFile) -> tuple[str, str, dict]:
        """
        Сохраняет видеофайл с валидацией
        Возвращает: (full_path, relative_path, file_info)
        """
        # Валидируем файл
        self.validate_video_file(file)
        
        # Сохраняем в папку uploads
        full_path, relative_path = await self.save_upload_file(file, "uploads")
        
        # Собираем информацию о файле
        file_info = {
            'original_filename': file.filename,
            'filename': os.path.basename(full_path),
            'file_size': os.path.getsize(full_path),
            'mime_type': file.content_type or 'video/mp4',
            'file_path': relative_path
        }
        
        return full_path, relative_path, file_info
    
    def delete_file(self, file_path: str) -> bool:
        """Удаляет файл"""
        try:
            if os.path.isabs(file_path):
                full_path = file_path
            else:
                full_path = os.path.join(self.storage_path, file_path)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"File deleted: {full_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {full_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def get_file_url(self, file_path: str, base_url: str = "") -> str:
        """Генерирует URL для доступа к файлу"""
        if not file_path:
            return ""
        
        # Убираем начальный слэш если есть
        clean_path = file_path.lstrip('/')
        
        if base_url:
            return f"{base_url.rstrip('/')}/files/{clean_path}"
        else:
            return f"/files/{clean_path}"
    
    def get_full_path(self, relative_path: str) -> str:
        """Преобразует относительный путь в полный"""
        return os.path.join(self.storage_path, relative_path.lstrip('/'))
    
    def file_exists(self, file_path: str) -> bool:
        """Проверяет существование файла"""
        if os.path.isabs(file_path):
            return os.path.exists(file_path)
        else:
            full_path = os.path.join(self.storage_path, file_path)
            return os.path.exists(full_path)
    
    def get_file_size(self, file_path: str) -> int:
        """Возвращает размер файла в байтах"""
        try:
            if os.path.isabs(file_path):
                full_path = file_path
            else:
                full_path = os.path.join(self.storage_path, file_path)
            
            if os.path.exists(full_path):
                return os.path.getsize(full_path)
            else:
                return 0
                
        except Exception:
            return 0
    
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """Очищает временные файлы старше указанного времени"""
        import time
        
        temp_dir = os.path.join(self.storage_path, 'temp')
        if not os.path.exists(temp_dir):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Deleted old temp file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")


# Глобальный экземпляр
file_handler = FileHandler()