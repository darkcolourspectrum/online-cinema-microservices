from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.movies import router as movies_router
from .api.genres import router as genres_router
from .core.config import settings

# Создаем приложение FastAPI
app = FastAPI(
    title=settings.service_name,
    description="Movie catalog microservice",
    version="1.0.0"
)

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(movies_router)
app.include_router(genres_router)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": settings.service_name,
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)