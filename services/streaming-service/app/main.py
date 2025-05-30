from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api.streaming import router as streaming_router
from .api.upload import router as upload_router
from .core.config import settings
import os

app = FastAPI(
    title=settings.service_name,
    description="Video Streaming and Upload microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(streaming_router)
app.include_router(upload_router)

# Статические файлы для доступа к видео и изображениям
if os.path.exists(settings.storage_path):
    app.mount(
        "/files", 
        StaticFiles(directory=settings.storage_path), 
        name="files"
    )


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": settings.service_name,
        "status": "running",
        "version": "1.0.0",
        "features": [
            "Video upload and processing",
            "Multi-quality video streaming",
            "Watch session tracking",
            "Streaming statistics",
            "Thumbnail generation",
            "Progress tracking",
            "User watch history"
        ],
        "supported_formats": settings.allowed_video_formats_list,
        "supported_qualities": settings.supported_qualities_list,
        "max_file_size_mb": settings.max_file_size_mb
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)