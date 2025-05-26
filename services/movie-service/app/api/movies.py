from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..core.database import get_db
from ..models.movie import Movie
from ..models.genre import Genre
from ..schemas.movie import MovieCreate, MovieUpdate, Movie as MovieSchema, MovieList
from ..utils.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=MovieList)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    genre_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Получить список фильмов с пагинацией и фильтрацией"""
    query = db.query(Movie).filter(Movie.is_available == True)
    
    # Поиск по названию и описанию
    if search:
        query = query.filter(
            or_(
                Movie.title.ilike(f"%{search}%"),
                Movie.description.ilike(f"%{search}%"),
                Movie.director.ilike(f"%{search}%")
            )
        )
    
    # Фильтр по жанру
    if genre_id:
        query = query.join(Movie.genres).filter(Genre.id == genre_id)
    
    # Подсчет общего количества
    total = query.count()
    
    # Пагинация
    movies = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return MovieList(
        movies=movies,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{movie_id}", response_model=MovieSchema)
async def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Получить фильм по ID"""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    return movie


@router.post("/", response_model=MovieSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie: MovieCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Только для авторизованных
):
    """Создать новый фильм (только для авторизованных пользователей)"""
    # Создаем фильм
    db_movie = Movie(
        title=movie.title,
        description=movie.description,
        release_year=movie.release_year,
        duration_minutes=movie.duration_minutes,
        director=movie.director,
        cast=movie.cast,
        poster_url=movie.poster_url,
        trailer_url=movie.trailer_url,
        video_url=movie.video_url,
        imdb_rating=movie.imdb_rating
    )
    
    # Добавляем жанры
    if movie.genre_ids:
        genres = db.query(Genre).filter(Genre.id.in_(movie.genre_ids)).all()
        db_movie.genres = genres
    
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


@router.put("/{movie_id}", response_model=MovieSchema)
async def update_movie(
    movie_id: int,
    movie_update: MovieUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновить фильм (только для авторизованных пользователей)"""
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    # Обновляем поля
    update_data = movie_update.dict(exclude_unset=True)
    
    # Обрабатываем жанры отдельно
    if "genre_ids" in update_data:
        genre_ids = update_data.pop("genre_ids")
        if genre_ids is not None:
            genres = db.query(Genre).filter(Genre.id.in_(genre_ids)).all()
            db_movie.genres = genres
    
    # Обновляем остальные поля
    for field, value in update_data.items():
        setattr(db_movie, field, value)
    
    db.commit()
    db.refresh(db_movie)
    return db_movie


@router.delete("/{movie_id}")
async def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Удалить фильм (только для авторизованных пользователей)"""
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    db.delete(db_movie)
    db.commit()
    return {"message": "Movie deleted successfully"}