from fastapi import Depends, HTTPException, status, Request
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


def get_client_info(request: Request) -> dict:
    """Получает информацию о клиенте для логирования сессий"""
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Определяем тип устройства на основе User-Agent
    device_type = "desktop"
    ua_lower = user_agent.lower()
    
    if any(mobile in ua_lower for mobile in ["mobile", "android", "iphone", "ipod"]):
        device_type = "mobile"
    elif any(tablet in ua_lower for tablet in ["tablet", "ipad"]):
        device_type = "tablet"
    elif any(tv in ua_lower for tv in ["smart-tv", "roku", "chromecast", "appletv"]):
        device_type = "tv"
    
    # IP адрес
    ip_address = request.client.host if request.client else "Unknown"
    
    # заголовки для реального IP (если за прокси/load balancer)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        ip_address = real_ip
    
    return {
        "user_agent": user_agent,
        "device_type": device_type,
        "ip_address": ip_address
    }