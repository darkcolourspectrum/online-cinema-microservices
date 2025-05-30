import os
import ffmpeg # type: ignore
import asyncio
from typing import Dict, Any, Optional, Tuple
from PIL import Image # type: ignore
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Класс для обработки видеофайлов с помощью FFmpeg"""
    
    def __init__(self):
        self.storage_path = settings.storage_path
        self.supported_qualities = settings.supported_qualities_list
        
    async def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """Получает информацию о видеофайле"""
        try:
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            info = {
                'duration': float(probe['format'].get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'bitrate': int(probe['format'].get('bit_rate', 0)) // 1000,  # Convert to kbps
                'fps': self._get_fps(video_stream),
                'codec': video_stream.get('codec_name'),
                'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
                'file_format': probe['format'].get('format_name'),
                'file_size': int(probe['format'].get('size', 0)),
                'creation_time': probe['format'].get('tags', {}).get('creation_time')
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting video info for {file_path}: {str(e)}")
            raise
    
    def _get_fps(self, video_stream: Dict) -> float:
        """Извлекает FPS из потока видео"""
        fps_str = video_stream.get('r_frame_rate', '0/1')
        try:
            num, den = map(int, fps_str.split('/'))
            return round(num / den, 2) if den != 0 else 0.0
        except:
            return 0.0
    
    async def create_thumbnail(self, video_path: str, output_path: str, timestamp: float = 10.0) -> bool:
        """Создает миниатюру видео"""
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Создаем скриншот
            (
                ffmpeg
                .input(video_path, ss=timestamp)
                .output(output_path, vframes=1, format='image2', vcodec='png')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # Изменяем размер до нужных размеров
            if os.path.exists(output_path):
                await self._resize_image(output_path, settings.thumbnail_width, settings.thumbnail_height)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            return False
    
    async def _resize_image(self, image_path: str, width: int, height: int):
        """Изменяет размер изображения"""
        try:
            with Image.open(image_path) as img:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                img.save(image_path, optimize=True, quality=85)
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
    
    async def create_preview_gif(self, video_path: str, output_path: str, duration: int = 3) -> bool:
        """Создает GIF превью видео"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            (
                ffmpeg
                .input(video_path, ss=30, t=duration)
                .output(output_path, vf='scale=320:180:flags=lanczos,fps=10', format='gif')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            return os.path.exists(output_path)
            
        except Exception as e:
            logger.error(f"Error creating preview GIF: {str(e)}")
            return False
    
    async def convert_video_quality(self, input_path: str, output_path: str, quality: str) -> bool:
        """Конвертирует видео в указанное качество"""
        try:
            quality_settings = self._get_quality_settings(quality)
            if not quality_settings:
                return False
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Создаем FFmpeg команду
            stream = ffmpeg.input(input_path)
            
            # Применяем настройки качества
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec='libx264',
                acodec='aac',
                preset='medium',
                crf=quality_settings['crf'],
                vf=f"scale={quality_settings['width']}:{quality_settings['height']}",
                maxrate=f"{quality_settings['bitrate']}k",
                bufsize=f"{quality_settings['bitrate'] * 2}k",
                format='mp4',
                movflags='faststart'  # Для веб-стриминга
            )
            
            # Запускаем конвертацию
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            return os.path.exists(output_path)
            
        except Exception as e:
            logger.error(f"Error converting video to {quality}: {str(e)}")
            return False
    
    def _get_quality_settings(self, quality: str) -> Optional[Dict[str, Any]]:
        """Возвращает настройки для указанного качества"""
        quality_map = {
            '480p': {'width': 854, 'height': 480, 'bitrate': 1000, 'crf': 23},
            '720p': {'width': 1280, 'height': 720, 'bitrate': 2500, 'crf': 21},
            '1080p': {'width': 1920, 'height': 1080, 'bitrate': 5000, 'crf': 19},
            '1440p': {'width': 2560, 'height': 1440, 'bitrate': 8000, 'crf': 17},
            '2160p': {'width': 3840, 'height': 2160, 'bitrate': 15000, 'crf': 15}
        }
        
        return quality_map.get(quality)
    
    async def process_video_async(self, video_id: int, input_path: str, callback=None) -> Dict[str, Any]:
        """Асинхронная обработка видео с callback для обновления прогресса"""
        results = {
            'video_id': video_id,
            'status': 'processing',
            'qualities_created': [],
            'thumbnail_created': False,
            'preview_created': False,
            'errors': []
        }
        
        try:
            # Получаем информацию о видео
            video_info = await self.get_video_info(input_path)
            original_height = video_info.get('height', 0)
            
            # Определяем какие качества нужно создать
            qualities_to_create = self._get_applicable_qualities(original_height)
            total_tasks = len(qualities_to_create) + 2  # +2 для thumbnail и preview
            completed_tasks = 0
            
            if callback:
                await callback(video_id, 'processing', completed_tasks / total_tasks)
            
            # Создаем миниатюру
            thumbnail_path = os.path.join(
                self.storage_path, 'thumbnails', f"video_{video_id}_thumb.png"
            )
            
            if await self.create_thumbnail(input_path, thumbnail_path):
                results['thumbnail_created'] = True
                results['thumbnail_path'] = thumbnail_path
            else:
                results['errors'].append("Failed to create thumbnail")
            
            completed_tasks += 1
            if callback:
                await callback(video_id, 'processing', completed_tasks / total_tasks)
            
            # Создаем GIF превью
            preview_path = os.path.join(
                self.storage_path, 'thumbnails', f"video_{video_id}_preview.gif"
            )
            
            if await self.create_preview_gif(input_path, preview_path):
                results['preview_created'] = True
                results['preview_path'] = preview_path
            else:
                results['errors'].append("Failed to create preview GIF")
            
            completed_tasks += 1
            if callback:
                await callback(video_id, 'processing', completed_tasks / total_tasks)
            
            # Конвертируем в разные качества
            for quality in qualities_to_create:
                output_path = os.path.join(
                    self.storage_path, 'videos', f"video_{video_id}_{quality}.mp4"
                )
                
                if await self.convert_video_quality(input_path, output_path, quality):
                    results['qualities_created'].append({
                        'quality': quality,
                        'path': output_path,
                        'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0
                    })
                else:
                    results['errors'].append(f"Failed to create {quality} quality")
                
                completed_tasks += 1
                if callback:
                    await callback(video_id, 'processing', completed_tasks / total_tasks)
            
            # Определяем финальный статус
            if results['qualities_created']:
                results['status'] = 'completed'
            else:
                results['status'] = 'failed'
                results['errors'].append("No qualities were successfully created")
            
            if callback:
                await callback(video_id, results['status'], 1.0)
            
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(f"Processing error: {str(e)}")
            logger.error(f"Video processing failed for video {video_id}: {str(e)}")
            
            if callback:
                await callback(video_id, 'failed', 1.0)
        
        return results
    
    def _get_applicable_qualities(self, original_height: int) -> list:
        """Определяет какие качества нужно создать на основе оригинального разрешения"""
        quality_heights = {
            '480p': 480,
            '720p': 720,
            '1080p': 1080,
            '1440p': 1440,
            '2160p': 2160
        }
        
        applicable = []
        for quality in self.supported_qualities:
            if quality in quality_heights and quality_heights[quality] <= original_height:
                applicable.append(quality)
        
        # Всегда включаем 480p для совместимости
        if '480p' not in applicable and original_height >= 480:
            applicable.append('480p')
        
        return sorted(applicable, key=lambda q: quality_heights.get(q, 0))
    
    def get_video_duration_formatted(self, duration_seconds: float) -> str:
        """Форматирует длительность видео в читаемый вид"""
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


# Глобальный экземпляр
video_processor = VideoProcessor()