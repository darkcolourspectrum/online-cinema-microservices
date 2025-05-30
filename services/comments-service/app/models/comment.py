from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    
    movie_id = Column(Integer, nullable=False, index=True)
    
    user_email = Column(String, nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    
    rating = Column(Integer, nullable=True)  # может быть None если только текст
    
    user_display_name = Column(String, nullable=True)  # Имя пользователя (кэш)
    movie_title = Column(String, nullable=True)  # Название фильма (кэш)
    
    is_approved = Column(Boolean, default=True)  # Автоматическое одобрение
    is_hidden = Column(Boolean, default=False)   # Скрыт модератором
    
    parent_id = Column(Integer, ForeignKey('comments.id'), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Comment", back_populates="replies", remote_side=[id])


class CommentLike(Base):
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True)
    
    comment_id = Column(Integer, ForeignKey('comments.id'), nullable=False)
    user_email = Column(String, nullable=False)
    
    # True = лайк, False = дизлайк
    is_like = Column(Boolean, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    
    comment = relationship("Comment")
    
    # один пользователь может поставить только один лайк/дизлайк на комментарий
    __table_args__ = (
        UniqueConstraint('comment_id', 'user_email', name='_comment_user_like'),
    )