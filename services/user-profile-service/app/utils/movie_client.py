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
    
    async def get_movies_by_ids(self, movie_ids: list[int]) -> Dict[int, Dict[Any, Any]]:
        """Получить информацию о нескольких фильмах по их ID"""
        movies = {}
        try:
            async with httpx.AsyncClient() as client:
                for movie_id in movie_ids:
                    response = await client.get(f"{self.base_url}/movies/{movie_id}")
                    if response.status_code == 200:
                        movies[movie_id] = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError):
            pass
        return movies
    
    async def search_movies(self, query: str, limit: int = 10) -> list[Dict[Any, Any]]:
        """Поиск фильмов"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/movies/",
                    params={"search": query, "per_page": limit}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("movies", [])
                return []
        except (httpx.RequestError, httpx.HTTPStatusError):
            return []
    
    async def get_genres(self) -> list[Dict[Any, Any]]:
        """Получить все жанры"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/genres/")
                if response.status_code == 200:
                    return response.json()
                return []
        except (httpx.RequestError, httpx.HTTPStatusError):
            return []


movie_client = MovieServiceClient()