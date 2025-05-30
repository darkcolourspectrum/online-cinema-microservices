from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from ..core.database import get_db
from ..models.comment import Comment, CommentLike
from ..schemas.comment import (
    CommentCreate,
    CommentUpdate,
    Comment as CommentSchema,
    CommentWithReplies,
    CommentsList,
    CommentLikeCreate,
    CommentStats
)
from ..utils.auth import get_current_user, get_current_user_optional
from ..utils.movie_client import movie_client

router = APIRouter(prefix="/comments", tags=["Comments"])


def build_comment_tree(comments: List[Comment], parent_id: int = None) -> List[CommentWithReplies]:
    """Построение древовидной структуры комментариев"""
    tree = []
    for comment in comments:
        if comment.parent_id == parent_id:
            comment_dict = {
                "id": comment.id,
                "movie_id": comment.movie_id,
                "content": comment.content,
                "rating": comment.rating,
                "parent_id": comment.parent_id,
                "user_email": comment.user_email,
                "user_display_name": comment.user_display_name,
                "movie_title": comment.movie_title,
                "is_approved": comment.is_approved,
                "is_hidden": comment.is_hidden,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "likes_count": 0,  # TODO: подсчет лайков
                "dislikes_count": 0,  # TODO: подсчет дизлайков
                "user_reaction": None,  # TODO: реакция пользователя
                "replies": build_comment_tree(comments, comment.id)
            }
            tree.append(CommentWithReplies(**comment_dict))
    return tree


@router.get("/movie/{movie_id}", response_model=CommentsList)
async def get_movie_comments(
    movie_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|rating|likes)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Получить комментарии для фильма"""
    
    # Проверяем, существует ли фильм
    if not await movie_client.verify_movie_exists(movie_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    # Базовый запрос - только основные комментарии (без родителя)
    query = db.query(Comment).filter(
        and_(
            Comment.movie_id == movie_id,
            Comment.is_approved == True,
            Comment.is_hidden == False,
            Comment.parent_id.is_(None)
        )
    )
    
    # Сортировка
    if sort_by == "created_at":
        if order == "desc":
            query = query.order_by(desc(Comment.created_at))
        else:
            query = query.order_by(Comment.created_at)
    elif sort_by == "rating":
        if order == "desc":
            query = query.order_by(desc(Comment.rating))
        else:
            query = query.order_by(Comment.rating)
    
    # Подсчет общего количества
    total = query.count()
    
    # Получаем основные комментарии с пагинацией
    main_comments = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Получаем все ответы для отображаемых комментариев
    main_comment_ids = [c.id for c in main_comments]
    all_replies = db.query(Comment).filter(
        and_(
            Comment.movie_id == movie_id,
            Comment.is_approved == True,
            Comment.is_hidden == False,
            Comment.parent_id.in_(main_comment_ids)
        )
    ).order_by(Comment.created_at).all()
    
    # Объединяем основные комментарии с ответами
    all_comments = main_comments + all_replies
    
    # Строим древовидную структуру
    comments_tree = build_comment_tree(all_comments)
    
    # Подсчитываем средний рейтинг
    avg_rating = db.query(func.avg(Comment.rating)).filter(
        and_(
            Comment.movie_id == movie_id,
            Comment.rating.isnot(None),
            Comment.is_approved == True,
            Comment.is_hidden == False
        )
    ).scalar()
    
    return CommentsList(
        comments=comments_tree,
        total=total,
        page=page,
        per_page=per_page,
        average_rating=round(avg_rating, 1) if avg_rating else None
    )


@router.post("/", response_model=CommentSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать новый комментарий"""
    user_email = current_user["email"]
    
    # Проверяем, существует ли фильм
    movie_details = await movie_client.get_movie_by_id(comment_data.movie_id)
    if not movie_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    # Если это ответ на комментарий, проверяем существование родительского комментария
    if comment_data.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found"
            )
        if parent_comment.movie_id != comment_data.movie_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment belongs to different movie"
            )
    
    # Создаем комментарий
    comment = Comment(
        movie_id=comment_data.movie_id,
        user_email=user_email,
        content=comment_data.content,
        rating=comment_data.rating,
        parent_id=comment_data.parent_id,
        movie_title=movie_details.get("title"),
        user_display_name=user_email.split("@")[0]  # Простое имя из email
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment


@router.put("/{comment_id}", response_model=CommentSchema)
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить комментарий (только автор может редактировать)"""
    user_email = current_user["email"]
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment.user_email != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments"
        )
    
    # Обновляем поля
    update_data = comment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить комментарий (только автор может удалять)"""
    user_email = current_user["email"]
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment.user_email != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )
    
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}


@router.post("/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    like_data: CommentLikeCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Поставить лайк/дизлайк комментарию"""
    user_email = current_user["email"]
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Проверяем существующую реакцию
    existing_like = db.query(CommentLike).filter(
        and_(CommentLike.comment_id == comment_id, CommentLike.user_email == user_email)
    ).first()
    
    if existing_like:
        if existing_like.is_like == like_data.is_like:
            # Убираем реакцию
            db.delete(existing_like)
            db.commit()
            return {"message": "Reaction removed"}
        else:
            # Меняем реакцию
            existing_like.is_like = like_data.is_like
            db.commit()
            return {"message": "Reaction updated"}
    else:
        # Создаем новую реакцию
        new_like = CommentLike(
            comment_id=comment_id,
            user_email=user_email,
            is_like=like_data.is_like
        )
        db.add(new_like)
        db.commit()
        return {"message": "Reaction added"}


@router.get("/movie/{movie_id}/stats", response_model=CommentStats)
async def get_movie_comment_stats(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Получить статистику комментариев для фильма"""
    
    # Проверяем, существует ли фильм
    if not await movie_client.verify_movie_exists(movie_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    # Общее количество комментариев
    total_comments = db.query(Comment).filter(
        and_(
            Comment.movie_id == movie_id,
            Comment.is_approved == True,
            Comment.is_hidden == False
        )
    ).count()
    
    # Средний рейтинг
    avg_rating = db.query(func.avg(Comment.rating)).filter(
        and_(
            Comment.movie_id == movie_id,
            Comment.rating.isnot(None),
            Comment.is_approved == True,
            Comment.is_hidden == False
        )
    ).scalar()
    
    # Распределение рейтингов
    rating_dist = db.query(
        Comment.rating,
        func.count(Comment.rating)
    ).filter(
        and_(
            Comment.movie_id == movie_id,
            Comment.rating.isnot(None),
            Comment.is_approved == True,
            Comment.is_hidden == False
        )
    ).group_by(Comment.rating).all()
    
    rating_distribution = {rating: count for rating, count in rating_dist}
    
    # Последние комментарии
    recent_comments = db.query(Comment).filter(
        and_(
            Comment.movie_id == movie_id,
            Comment.is_approved == True,
            Comment.is_hidden == False
        )
    ).order_by(desc(Comment.created_at)).limit(5).all()
    
    return CommentStats(
        total_comments=total_comments,
        average_rating=round(avg_rating, 1) if avg_rating else None,
        rating_distribution=rating_distribution,
        recent_comments=recent_comments
    )