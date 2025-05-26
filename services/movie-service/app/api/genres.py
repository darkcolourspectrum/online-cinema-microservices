from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.genre import Genre
from ..schemas.movie import GenreCreate, Genre as GenreSchema
from ..utils.auth import get_current_user

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("/", response_model=List[GenreSchema])
async def get_genres(db: Session = Depends(get_db)):
    """Получить все жанры"""
    genres = db.query(Genre).all()
    return genres


@router.post("/", response_model=GenreSchema, status_code=status.HTTP_201_CREATED)
async def create_genre(
    genre: GenreCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Только для авторизованных
):
    """Создать новый жанр (только для авторизованных пользователей)"""
    # Проверяем, что жанр не существует
    existing_genre = db.query(Genre).filter(Genre.name == genre.name).first()
    if existing_genre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Genre already exists"
        )
    
    db_genre = Genre(name=genre.name, description=genre.description)
    db.add(db_genre)
    db.commit()
    db.refresh(db_genre)
    return db_genre


@router.get("/{genre_id}", response_model=GenreSchema)
async def get_genre(genre_id: int, db: Session = Depends(get_db)):
    """Получить жанр по ID"""
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found"
        )
    return genre