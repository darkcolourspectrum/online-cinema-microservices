from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import create_access_token
from ..schemas.user import UserCreate, UserLogin, UserResponse, Token
from ..utils.auth import create_user, authenticate_user, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    db_user = create_user(db, user)
    return db_user


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Вход пользователя"""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем JWT токен
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user


@router.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    """Пример защищенного эндпоинта"""
    return {
        "message": f"Hello {current_user.username}! This is a protected route.",
        "user_id": current_user.id
    }