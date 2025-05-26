from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.auth import router as auth_router
from .core.config import settings

app = FastAPI(
    title=settings.service_name,
    description="Authentication and Authorization microservice",
    version="1.0.0"
)

# Настройка CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(auth_router)


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