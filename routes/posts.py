from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from models.user import User
from schemas.comment import CommentResponse, CommentRequest
from schemas.post import PostResponse, MealStatisticsResponse
from app_utils.security import get_current_user
from services.post_service import PostService
from app_utils.dependencies import get_post_service

router = APIRouter()

@router.post("/", response_model=PostResponse)
def create_post(
        caption: str = Form(...),
        file: UploadFile = File(None),
        protein: int = Form(...),
        carbs: int = Form(...),
        fats: int = Form(...),
        current_user: User = Depends(get_current_user),
        service: PostService = Depends(get_post_service)
):
    macros = {"protein": protein, "carbs": carbs, "fats": fats, "calories": (protein * 4) + (carbs * 4) + (fats * 9)}
    return service.create_user_post(current_user.id, caption, file, macros)

@router.get("/feed", response_model=List[PostResponse])
def get_feed(current_user: User = Depends(get_current_user), service: PostService = Depends(get_post_service)):
    return service.get_user_feed(current_user.id)

@router.get("/{post_id}", response_model=PostResponse)
def get_post_by_id(post_id: int, service: PostService = Depends(get_post_service)):
    try:
        return service.get_post_by_id(post_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/{user_id}")
def get_user_posts(
    user_id: int,
    service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return service.get_user_posts(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/like")
def like_post(
        post_id: int,
        current_user: User = Depends(get_current_user),
        service: PostService = Depends(get_post_service)
):
    try:
        service.like_post(current_user.id, post_id)
        return service.get_post_by_id(post_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{post_id}/unlike")
def unlike_post(
        post_id: int,
        current_user: User = Depends(get_current_user),
        service: PostService = Depends(get_post_service)
):
    try:
        service.unlike_post(current_user.id, post_id)
        return service.get_post_by_id(post_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/comment", response_model=CommentResponse)
def comment_on_post(
        post_id: int,
        comment_data: CommentRequest,
        current_user: User = Depends(get_current_user),
        service: PostService = Depends(get_post_service)
):
    try:
        return service.comment_on_post(current_user.id, post_id, comment_data.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/posts/nutrition-statistics", response_model=MealStatisticsResponse)
def get_nutrition_statistics(
        start_date: str,
        end_date: str,
        service: PostService = Depends(get_post_service),
        current_user=Depends(get_current_user)
):
    try:
        return service.get_user_nutrition_statistics(current_user.id, start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
