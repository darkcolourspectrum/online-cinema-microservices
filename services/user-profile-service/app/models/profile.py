from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from ..core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    
    user_email = Column(String, unique=True, index=True, nullable=False)
    
    display_name = Column(String, nullable=True)  
    bio = Column(Text, nullable=True)  
    avatar_url = Column(String, nullable=True)  
    
    preferred_genres = Column(JSON, nullable=True)  
    language = Column(String, default='en', nullable=False)  
    notifications_enabled = Column(Boolean, default=True)  
    
    movies_watched = Column(Integer, default=0)  
    total_watch_time = Column(Integer, default=0)  
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True) 