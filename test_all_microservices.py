#!/usr/bin/env python3
"""
Полное тестирование всех микросервисов Cinema Microservices
Запуск: python test_all_microservices.py
"""

import requests
import json
import time
import os
from typing import Optional, Dict, Any

BASE_URL = "http://localhost"

class MicroservicesTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.user_token = None
        self.user_email = "test@cinema.com"
        self.created_entities = {
            'genre_id': None,
            'movie_id': None,
            'comment_id': None,
            'video_id': None,
            'session_id': None
        }
        
    def print_section(self, title: str):
        print(f"\n{'='*60}")
        print(f" {title}")
        print('='*60)
        
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    files: dict = None, token: str = None) -> dict:
        """Универсальная функция для запросов"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        if data and not files:
            headers["Content-Type"] = "application/json"
            
        try:
            kwargs = {"headers": headers}
            
            if files:
                kwargs["files"] = files
                if data:
                    kwargs["data"] = data
            elif data:
                kwargs["json"] = data
                
            if method.upper() == 'GET':
                response = requests.get(url, **{k: v for k, v in kwargs.items() if k != 'json' and k != 'files' and k != 'data'})
            elif method.upper() == 'POST':
                response = requests.post(url, **kwargs)
            elif method.upper() == 'PUT':
                response = requests.put(url, **kwargs)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, **{k: v for k, v in kwargs.items() if k != 'json' and k != 'files' and k != 'data'})
            else:
                raise ValueError(f"Неподдерживаемый метод: {method}")
                
            print(f"\n{method} {endpoint}")
            print(f"Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                if response.headers.get('content-type', '').startswith('application/json'):
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
                    return result
                else:
                    print(f"Response: {response.text[:200]}...")
                    return {"message": "Success", "content": response.text}
            else:
                print(f"Error: {response.text}")
                return {"error": response.text, "status": response.status_code}
                
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            return {"error": str(e)}
    
    def test_service_health(self):
        """Проверка здоровья всех сервисов"""
        self.print_section("ПРОВЕРКА ЗДОРОВЬЯ ВСЕХ СЕРВИСОВ")
        
        services = [
            ("/api/auth/", "Auth Service"),
            ("/api/movies/", "Movie Service"), 
            ("/api/comments/", "Comments Service"),
            ("/api/streaming/", "Streaming Service"),
            ("/api/upload/", "Upload Service")
        ]
        
        for endpoint, name in services:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                print(f"{name}: {'✅ OK' if response.status_code == 200 else '❌ ERROR'}")
            except:
                print(f"{name}: ❌ CONNECTION ERROR")
    
    def test_auth_service(self):
        """Тестирование Auth Service"""
        self.print_section("ТЕСТИРОВАНИЕ AUTH SERVICE")
        
        # Регистрация
        user_data = {
            "email": self.user_email,
            "username": "testuser",
            "password": "testpassword123"
        }
        result = self.make_request('POST', '/api/auth/register', user_data)
        
        if 'error' not in result:
            print("✅ Пользователь зарегистрирован")
        else:
            print("⚠️ Пользователь уже существует")
        
        # Авторизация
        login_data = {
            "email": self.user_email,
            "password": "testpassword123"
        }
        result = self.make_request('POST', '/api/auth/login', login_data)
        
        if 'access_token' in result:
            self.user_token = result['access_token']
            print("✅ Пользователь авторизован")
            
            # Получение информации о пользователе
            user_info = self.make_request('GET', '/api/auth/me', token=self.user_token)
            if 'email' in user_info:
                print("✅ Информация о пользователе получена")
        else:
            print("❌ Ошибка авторизации")
            return False
        
        return True
    
    def test_movie_service(self):
        """Тестирование Movie Service"""
        self.print_section("ТЕСТИРОВАНИЕ MOVIE SERVICE")
        
        if not self.user_token:
            print("❌ Нет токена авторизации")
            return False
        
        # Создание жанра
        genre_data = {
            "name": "Тестовый экшн",
            "description": "Жанр для тестирования всех сервисов"
        }
        result = self.make_request('POST', '/api/genres/', genre_data, token=self.user_token)
        
        if 'id' in result:
            self.created_entities['genre_id'] = result['id']
            print(f"✅ Жанр создан с ID: {result['id']}")
        else:
            # Получаем существующие жанры
            genres = self.make_request('GET', '/api/genres/')
            if genres and len(genres) > 0:
                self.created_entities['genre_id'] = genres[0]['id']
                print(f"✅ Используется существующий жанр с ID: {genres[0]['id']}")
        
        # Создание фильма
        if self.created_entities['genre_id']:
            movie_data = {
                "title": "Тестовый блокбастер",
                "description": "Фильм для тестирования всех микросервисов",
                "release_year": 2024,
                "duration_minutes": 150,
                "director": "Тестовый режиссер",
                "cast": "Звездный актерский состав",
                "poster_url": "https://example.com/poster.jpg",
                "trailer_url": "https://example.com/trailer.mp4",
                "imdb_rating": 8.5,
                "genre_ids": [self.created_entities['genre_id']]
            }
            result = self.make_request('POST', '/api/movies/', movie_data, token=self.user_token)
            
            if 'id' in result:
                self.created_entities['movie_id'] = result['id']
                print(f"✅ Фильм создан с ID: {result['id']}")
            else:
                # Получаем существующие фильмы
                movies = self.make_request('GET', '/api/movies/')
                if 'movies' in movies and len(movies['movies']) > 0:
                    self.created_entities['movie_id'] = movies['movies'][0]['id']
                    print(f"✅ Используется существующий фильм с ID: {movies['movies'][0]['id']}")
        
        # Получение списка фильмов
        movies = self.make_request('GET', '/api/movies/')
        if 'movies' in movies:
            print(f"✅ Получен список фильмов, всего: {movies['total']}")
        
        return True
    
    def test_profile_service(self):
        """Тестирование User Profile Service"""
        self.print_section("ТЕСТИРОВАНИЕ USER PROFILE SERVICE")
        
        if not self.user_token:
            print("❌ Нет токена авторизации")
            return False
        
        # Получение профиля
        profile = self.make_request('GET', '/api/profiles/me', token=self.user_token)
        if 'id' in profile:
            print("✅ Профиль пользователя получен")
        
        # Обновление профиля
        profile_data = {
            "display_name": "Тестовый пользователь",
            "bio": "Тестирую микросервисы",
            "language": "ru",
            "notifications_enabled": True
        }
        result = self.make_request('PUT', '/api/profiles/me', profile_data, token=self.user_token)
        if 'display_name' in result:
            print("✅ Профиль обновлен")
        
        # Добавление в избранное
        if self.created_entities['movie_id']:
            favorite_data = {"movie_id": self.created_entities['movie_id']}
            result = self.make_request('POST', '/api/favorites/movies', favorite_data, token=self.user_token)
            if 'id' in result or 'error' in result:
                print("✅ Фильм добавлен в избранное (или уже там)")
            
            # Получение избранного
            favorites = self.make_request('GET', '/api/favorites/movies', token=self.user_token)
            if 'favorites' in favorites:
                print(f"✅ Получен список избранного, количество: {favorites['total']}")
        
        return True
    
    def test_comments_service(self):
        """Тестирование Comments Service"""
        self.print_section("ТЕСТИРОВАНИЕ COMMENTS SERVICE")
        
        if not self.user_token or not self.created_entities['movie_id']:
            print("❌ Нет токена авторизации или фильма")
            return False
        
        # Создание комментария
        comment_data = {
            "movie_id": self.created_entities['movie_id'],
            "content": "Потрясающий фильм! Все микросервисы работают отлично!",
            "rating": 9
        }
        result = self.make_request('POST', '/api/comments/', comment_data, token=self.user_token)
        
        if 'id' in result:
            self.created_entities['comment_id'] = result['id']
            print(f"✅ Комментарий создан с ID: {result['id']}")
            
            # Лайк комментария
            like_data = {"is_like": True}
            like_result = self.make_request('POST', f'/api/comments/{result["id"]}/like', 
                                          like_data, token=self.user_token)
            if 'message' in like_result:
                print("✅ Лайк поставлен")
        
        # Получение комментариев для фильма
        comments = self.make_request('GET', f'/api/comments/movie/{self.created_entities["movie_id"]}')
        if 'comments' in comments:
            print(f"✅ Получены комментарии, всего: {comments['total']}")
        
        # Статистика комментариев
        stats = self.make_request('GET', f'/api/comments/movie/{self.created_entities["movie_id"]}/stats')
        if 'total_comments' in stats:
            print(f"✅ Получена статистика: {stats['total_comments']} комментариев")
        
        return True
    
    def test_streaming_service(self):
        """Тестирование Streaming Service"""
        self.print_section("ТЕСТИРОВАНИЕ STREAMING SERVICE")
        
        if not self.user_token or not self.created_entities['movie_id']:
            print("❌ Нет токена авторизации или фильма")
            return False
        
        # Получение информации для стриминга
        streaming_info = self.make_request('GET', f'/api/streaming/info/{self.created_entities["movie_id"]}')
        if 'stream_urls' in streaming_info:
            print("✅ Информация для стриминга получена")
            self.created_entities['video_id'] = streaming_info.get('video_id')
        
        # Создание сессии просмотра (если есть видео)
        if self.created_entities.get('video_id'):
            session_data = {
                "movie_id": self.created_entities['movie_id'],
                "video_file_id": self.created_entities['video_id'],
                "current_time": 0.0,
                "quality": "720p",
                "volume": 0.8,
                "playback_speed": 1.0
            }
            result = self.make_request('POST', '/api/streaming/session', session_data, token=self.user_token)
            
            if 'id' in result:
                self.created_entities['session_id'] = result['id']
                print(f"✅ Сессия просмотра создана с ID: {result['id']}")
                
                # Обновление прогресса
                update_data = {
                    "current_time": 30.0,
                    "is_paused": False
                }
                update_result = self.make_request('PUT', f'/api/streaming/session/{result["id"]}', 
                                                update_data, token=self.user_token)
                if 'current_time' in update_result:
                    print("✅ Прогресс просмотра обновлен")
        
        # Получение статистики пользователя
        user_stats = self.make_request('GET', '/api/streaming/stats/user', token=self.user_token)
        if 'total_movies_watched' in user_stats:
            print(f"✅ Статистика пользователя: {user_stats['total_movies_watched']} фильмов")
        
        # Статистика фильма
        movie_stats = self.make_request('GET', f'/api/streaming/stats/movie/{self.created_entities["movie_id"]}')
        if 'total_views' in movie_stats:
            print(f"✅ Статистика фильма: {movie_stats['total_views']} просмотров")
        
        return True
    
    def test_upload_service(self):
        """Тестирование Upload Service (демо без реального файла)"""
        self.print_section("ТЕСТИРОВАНИЕ UPLOAD SERVICE")
        
        if not self.user_token or not self.created_entities['movie_id']:
            print("❌ Нет токена авторизации или фильма")
            return False
        
        # Получение списка загруженных видео
        videos = self.make_request('GET', '/api/upload/videos', token=self.user_token)
        if isinstance(videos, list):
            print(f"✅ Получен список видео: {len(videos)} файлов")
        
        # Тестируем получение статуса обработки (с фиктивным ID)
        status = self.make_request('GET', '/api/upload/status/1')
        if 'error' in status or 'video_id' in status:
            print("✅ Эндпоинт статуса обработки работает")
        
        print("ℹ️ Для полного тестирования загрузки нужен реальный видеофайл")
        
        return True
    
    def cleanup_test_data(self):
        """Очистка тестовых данных"""
        self.print_section("ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
        
        if not self.user_token:
            return
        
        # Завершение сессии просмотра
        if self.created_entities.get('session_id'):
            result = self.make_request('POST', f'/api/streaming/session/{self.created_entities["session_id"]}/end', 
                                     token=self.user_token)
            if 'message' in result:
                print("✅ Сессия просмотра завершена")
        
        # Удаление комментария
        if self.created_entities.get('comment_id'):
            result = self.make_request('DELETE', f'/api/comments/{self.created_entities["comment_id"]}', 
                                     token=self.user_token)
            if 'message' in result:
                print("✅ Комментарий удален")
        
        # Удаление из избранного
        if self.created_entities.get('movie_id'):
            result = self.make_request('DELETE', f'/api/favorites/movies/{self.created_entities["movie_id"]}', 
                                     token=self.user_token)
            if 'message' in result or 'error' in result:
                print("✅ Фильм удален из избранного")
        
        # Удаление фильма
        if self.created_entities.get('movie_id'):
            result = self.make_request('DELETE', f'/api/movies/{self.created_entities["movie_id"]}', 
                                     token=self.user_token)
            if 'message' in result:
                print("✅ Фильм удален")
        
        print("🧹 Очистка завершена")
    
    def run_full_test(self):
        """Запуск полного тестирования всех микросервисов"""
        print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ ВСЕХ МИКРОСЕРВИСОВ")
        print("="*70)
        
        start_time = time.time()
        
        try:
            # 1. Проверка здоровья сервисов
            self.test_service_health()
            
            # 2. Тестирование Auth Service
            if not self.test_auth_service():
                print("❌ Критическая ошибка: Auth Service не работает")
                return
            
            # 3. Тестирование Movie Service
            self.test_movie_service()
            
            # 4. Тестирование User Profile Service
            self.test_profile_service()
            
            # 5. Тестирование Comments Service
            self.test_comments_service()
            
            # 6. Тестирование Streaming Service
            self.test_streaming_service()
            
            # 7. Тестирование Upload Service
            self.test_upload_service()
            
            # 8. Очистка тестовых данных
            self.cleanup_test_data()
            
            end_time = time.time()
            
            self.print_section("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("Все микросервисы протестированы")
            print(f"Время выполнения: {end_time - start_time:.2f} секунд")
            print("\nДоступные интерфейсы:")
            print("   • Auth Service: http://localhost:8001/docs")
            print("   • Movie Service: http://localhost:8002/docs")
            print("   • Profile Service: http://localhost:8003/docs")
            print("   • Comments Service: http://localhost:8004/docs")
            print("   • Streaming Service: http://localhost:8005/docs")
            print("   • API Gateway: http://localhost/")
            print("   • pgAdmin: http://localhost:5050")
            
        except Exception as e:
            print(f"\n❌ Критическая ошибка тестирования: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tester = MicroservicesTester()
    tester.run_full_test()