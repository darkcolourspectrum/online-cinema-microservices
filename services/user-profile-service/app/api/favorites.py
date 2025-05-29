from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..core.database import get_db
from ..models.favorites import FavoriteMovie, WatchLater
from ..schemas.favorites import (
    FavoriteMovieCreate,
    FavoriteMovie as FavoriteMovieSchema,
    FavoriteMovieWithDetails,
    FavoritesList,
    WatchLaterCreate,
    WatchLaterUpdate,
    WatchLater as WatchLaterSchema,
    WatchLaterWithDetails,
    WatchLaterList
)
from ..utils.auth import get_current_user
from ..utils.movie_client import movie_client

router = APIRouter(prefix="/favorites", tags=["Favorites & Watch Later"])


# ========== ИЗБРАННЫЕ ФИЛЬМЫ ==========

@router.get("/movies", response_model=FavoritesList)
async def get_favorite_movies(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить список избранных фильмов"""
    user_email = current_user["email"]
    
    favorites = db.query(FavoriteMovie).filter(
        FavoriteMovie.user_email == user_email
    ).order_by(FavoriteMovie.added_at.desc()).all()
    
    # Получаем детальную информацию о фильмах из Movie Service
    movie_ids = [fav.movie_id for fav in favorites]
    movies_details = await movie_client.get_movies_by_ids(movie_ids)
    
    # Комбинируем данные
    favorites_with_details = []
    for favorite in favorites:
        favorite_dict = {
            "id": favorite.id,
            "user_email": favorite.user_email,
            "movie_id": favorite.movie_id,
            "movie_title": favorite.movie_title,
            "movie_poster_url": favorite.movie_poster_url,
            "added_at": favorite.added_at,
            "movie_details": movies_details.get(favorite.movie_id)
        }
        favorites_with_details.append(FavoriteMovieWithDetails(**favorite_dict))
    
    return FavoritesList(
        favorites=favorites_with_details,
        total=len(favorites)
    )


@router.post("/movies", response_model=FavoriteMovieSchema, status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    favorite_data: FavoriteMovieCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавить фильм в избранное"""
    user_email = current_user["email"]
    
    # Получаем информацию о фильме из Movie Service
    movie_details = await movie_client.get_movie_by_id(favorite_data.movie_id)
    if not movie_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    # Создаем запись в избранном
    favorite = FavoriteMovie(
        user_email=user_email,
        movie_id=favorite_data.movie_id,
        movie_title=movie_details.get("title"),
        movie_poster_url=movie_details.get("poster_url")
    )
    
    try:
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return favorite
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in favorites"
        )


@router.delete("/movies/{movie_id}")
async def remove_from_favorites(
    movie_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить фильм из избранного"""
    user_email = current_user["email"]
    
    favorite = db.query(FavoriteMovie).filter(
        FavoriteMovie.user_email == user_email,
        FavoriteMovie.movie_id == movie_id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not in favorites"
        )
    
    db.delete(favorite)
    db.commit()
    return {"message": "Movie removed from favorites"}


# ========== ПОСМОТРЕТЬ ПОЗЖЕ ==========

@router.get("/watch-later", response_model=WatchLaterList)
async def get_watch_later_movies(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить список фильмов 'посмотреть позже' """
    user_email = current_user["email"]
    
    watch_later_items = db.query(WatchLater).filter(
        WatchLater.user_email == user_email
    ).order_by(WatchLater.priority.desc(), WatchLater.added_at.desc()).all()
    
    # Получаем детальную информацию о фильмах
    movie_ids = [item.movie_id for item in watch_later_items]
    movies_details = await movie_client.get_movies_by_ids(movie_ids)
    
    # Комбинируем данные
    watch_later_with_details = []
    for item in watch_later_items:
        item_dict = {
            "id": item.id,
            "user_email": item.user_email,
            "movie_id": item.movie_id,
            "movie_title": item.movie_title,
            "movie_poster_url": item.movie_poster_url,
            "priority": item.priority,
            "added_at": item.added_at,
            "movie_details": movies_details.get(item.movie_id)
        }
        watch_later_with_details.append(WatchLaterWithDetails(**item_dict))
    
    return WatchLaterList(
        watch_later=watch_later_with_details,
        total=len(watch_later_items)
    )


@router.post("/watch-later", response_model=WatchLaterSchema, status_code=status.HTTP_201_CREATED)
async def add_to_watch_later(
    watch_later_data: WatchLaterCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавить фильм в список 'посмотреть позже' """
    user_email = current_user["email"]
    
    # Получаем информацию о фильме
    movie_details = await movie_client.get_movie_by_id(watch_later_data.movie_id)
    if not movie_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    # Создаем запись
    watch_later = WatchLater(
        user_email=user_email,
        movie_id=watch_later_data.movie_id,
        movie_title=movie_details.get("title"),
        movie_poster_url=movie_details.get("poster_url"),
        priority=watch_later_data.priority
    )
    
    try:
        db.add(watch_later)
        db.commit()
        db.refresh(watch_later)
        return watch_later
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in watch later list"
        )


@router.put("/watch-later/{movie_id}", response_model=WatchLaterSchema)
async def update_watch_later_priority(
    movie_id: int,
    update_data: WatchLaterUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить приоритет фильма в списке 'посмотреть позже' """
    user_email = current_user["email"]
    
    watch_later = db.query(WatchLater).filter(
        WatchLater.user_email == user_email,
        WatchLater.movie_id == movie_id
    ).first()
    
    if not watch_later:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not in watch later list"
        )
    
    if update_data.priority is not None:
        watch_later.priority = update_data.priority
    
    db.commit()
    db.refresh(watch_later)
    return watch_later


@router.delete("/watch-later/{movie_id}")
async def remove_from_watch_later(
    movie_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить фильм из списка 'посмотреть позже' """
    user_email = current_user["email"]
    
    watch_later = db.query(WatchLater).filter(
        WatchLater.user_email == user_email,
        WatchLater.movie_id == movie_id
    ).first()
    
    if not watch_later:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not in watch later list"
        )
    
    db.delete(watch_later)
    db.commit()
    return {"message": "Movie removed from watch later list"}