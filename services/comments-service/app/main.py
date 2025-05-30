from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.comments import router as comments_router
from .core.config import settings

app = FastAPI(
    title=settings.service_name,
    description="Comments and Ratings microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(comments_router)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": settings.service_name,
        "status": "running",
        "version": "1.0.0",
        "features": [
            "Movie comments",
            "Comment ratings",
            "Nested replies",
            "Like/Dislike system",
            "Comment moderation"
        ]
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)