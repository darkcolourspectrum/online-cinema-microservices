from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from ..core.config import settings

security = HTTPBearer()


def verify_token(token: str) -> dict:
    """Проверяет JWT токен и возвращает payload"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Получает текущего пользователя из JWT токена"""
    payload = verify_token(credentials.credentials)
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"email": email, "payload": payload}


def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))) -> dict:
    """Опциональная аутентификация - не выбрасывает ошибку если токена нет"""
    if credentials is None:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        email: str = payload.get("sub")
        return {"email": email, "payload": payload}
    except HTTPException:
        return None