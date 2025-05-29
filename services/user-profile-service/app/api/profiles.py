from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.database import get_db
from ..models.profile import UserProfile
from ..models.favorites import FavoriteMovie, WatchLater
from ..schemas.profile import (
    UserProfileCreate, 
    UserProfileUpdate, 
    UserProfile as UserProfileSchema,
    UserProfileStats,
    UserProfileWithStats
)
from ..utils.auth import get_current_user
from ..utils.movie_client import movie_client

router = APIRouter(prefix="/profiles", tags=["User Profiles"])


@router.get("/me", response_model=UserProfileSchema)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить мой профиль"""
    user_email = current_user["email"]
    
    profile = db.query(UserProfile).filter(UserProfile.user_email == user_email).first()
    if not profile:
        # Создаем профиль автоматически если его нет
        profile = UserProfile(user_email=user_email)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile


@router.put("/me", response_model=UserProfileSchema)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить мой профиль"""
    user_email = current_user["email"]
    
    profile = db.query(UserProfile).filter(UserProfile.user_email == user_email).first()
    if not profile:
        # Создаем профиль если его нет
        profile = UserProfile(user_email=user_email)
        db.add(profile)
    
    # Обновляем поля
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/stats", response_model=UserProfileStats)
async def get_my_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику моего профиля"""
    user_email = current_user["email"]
    
    # Получаем базовую статистику из профиля
    profile = db.query(UserProfile).filter(UserProfile.user_email == user_email).first()
    if not profile:
        profile = UserProfile(user_email=user_email)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    # Считаем избранные фильмы
    favorite_count = db.query(FavoriteMovie).filter(FavoriteMovie.user_email == user_email).count()
    
    # Считаем фильмы в списке "посмотреть позже"
    watch_later_count = db.query(WatchLater).filter(WatchLater.user_email == user_email).count()
    
    # TODO: Статистика по жанрам (пока заглушка)
    most_watched_genres = []
    
    return UserProfileStats(
        movies_watched=profile.movies_watched,
        total_watch_time=profile.total_watch_time,
        favorite_movies_count=favorite_count,
        watch_later_count=watch_later_count,
        most_watched_genres=most_watched_genres
    )


@router.get("/me/full", response_model=UserProfileWithStats)
async def get_my_full_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить полный профиль со статистикой"""
    # Получаем базовый профиль
    profile_response = await get_my_profile(current_user, db)
    
    # Получаем статистику
    stats_response = await get_my_stats(current_user, db)
    
    # Комбинируем данные
    profile_dict = profile_response.dict() if hasattr(profile_response, 'dict') else profile_response.__dict__
    stats_dict = stats_response.dict() if hasattr(stats_response, 'dict') else stats_response.__dict__
    
    return UserProfileWithStats(
        **profile_dict,
        stats=stats_dict
    )


@router.get("/{user_email}", response_model=UserProfileSchema)
async def get_user_profile(
    user_email: str,
    db: Session = Depends(get_db)
):
    """Получить публичный профиль пользователя по email"""
    profile = db.query(UserProfile).filter(UserProfile.user_email == user_email).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile