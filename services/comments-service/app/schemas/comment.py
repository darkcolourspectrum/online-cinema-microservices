from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class CommentBase(BaseModel):
    movie_id: int
    content: str = Field(..., min_length=1, max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=10)
    parent_id: Optional[int] = None


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=10)


class Comment(CommentBase):
    id: int
    user_email: str
    user_display_name: Optional[str]
    movie_title: Optional[str]
    is_approved: bool
    is_hidden: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Статистика лайков/дизлайков
    likes_count: int = 0
    dislikes_count: int = 0
    
    # Пользовательская реакция (если авторизован)
    user_reaction: Optional[bool] = None  # True=like, False=dislike, None=no reaction
    
    class Config:
        from_attributes = True


class CommentWithReplies(Comment):
    """Комментарий с ответами (для древовидной структуры)"""
    replies: List['CommentWithReplies'] = []


class CommentsList(BaseModel):
    """Список комментариев с пагинацией"""
    comments: List[CommentWithReplies]
    total: int
    page: int
    per_page: int
    average_rating: Optional[float] = None


class CommentLikeCreate(BaseModel):
    is_like: bool  # True = лайк, False = дизлайк


class CommentStats(BaseModel):
    """Статистика комментариев для фильма"""
    total_comments: int
    average_rating: Optional[float]
    rating_distribution: Dict[int, int]  # {1: 5, 2: 10, ...} количество оценок по звездам
    recent_comments: List[Comment] = []


CommentWithReplies.model_rebuild()