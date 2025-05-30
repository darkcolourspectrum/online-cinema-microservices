import httpx
from typing import Optional, Dict, Any
from ..core.config import settings


class MovieServiceClient:
    """Клиент для взаимодействия с Movie Service"""
    
    def __init__(self):
        self.base_url = settings.movie_service_url.rstrip('/')
    
    async def get_movie_by_id(self, movie_id: int) -> Optional[Dict[Any, Any]]:
        """Получить информацию о фильме по ID"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/movies/{movie_id}")
                if response.status_code == 200:
                    return response.json()
                return None
        except (httpx.RequestError, httpx.HTTPStatusError):
            return None
    
    async def verify_movie_exists(self, movie_id: int) -> bool:
        """Проверить, существует ли фильм"""
        movie = await self.get_movie_by_id(movie_id)
        return movie is not None


movie_client = MovieServiceClient()