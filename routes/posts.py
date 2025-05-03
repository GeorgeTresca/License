from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from models.user import User
from schemas.comment import CommentResponse, CommentRequest
from schemas.post import PostResponse
from app_utils.security import get_current_user
from services.social_service import SocialService
from app_utils.dependencies import get_social_service
from schemas.post import MealStatisticsResponse

router = APIRouter()


@router.post("/", response_model=PostResponse)
async def create_post(
        caption: str = Form(...),
        file: UploadFile = File(None),
        protein: int = Form(...),
        carbs: int = Form(...),
        fats: int = Form(...),
        current_user: User = Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    macros = {"protein": protein, "carbs": carbs, "fats": fats, "calories": (protein * 4) + (carbs * 4) + (fats * 9)}
    return await service.create_user_post(current_user.id, caption, file, macros)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
        post_id: int,
        caption: str = Form(None),
        file: UploadFile = File(None),
        protein: int = Form(None),
        carbs: int = Form(None),
        fats: int = Form(None),
        current_user: User = Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    macros = {"protein": protein, "carbs": carbs, "fats": fats,
              "calories": (protein * 4) + (carbs * 4) + (fats * 9)} if all(
        v is not None for v in [protein, carbs, fats]) else None
    try:
        return service.update_user_post(post_id, current_user.id, caption, file, macros)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{post_id}")
def delete_post(
        post_id: int,
        current_user: User = Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    try:
        return service.delete_user_post(post_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feed", response_model=List[PostResponse])
def get_feed(current_user: User = Depends(get_current_user), service: SocialService = Depends(get_social_service)):
    # return service.get_user_feed(current_user.id)
    feed = service.get_user_feed(current_user.id)

    # Add `username` for each post
    for post in feed:
        user = service.get_user_by_id(post.user_id)
        post.username = user.username

    return feed


@router.get("/{post_id}", response_model=PostResponse)
async def get_post_by_id(post_id: int, service: SocialService = Depends(get_social_service)):
    try:
        return service.get_post_by_id(post_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_posts(user_id: int,
                         service: SocialService = Depends(get_social_service),
                         current_user: User = Depends(get_current_user)):  # ✅ Requires authentication
    """
    API to retrieve all posts of a specific user.
    """
    try:
        return service.get_user_posts(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{post_id}/like")
async def like_post(
        post_id: int,
        current_user: User = Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    try:
        await service.like_post(current_user.id, post_id)
        return service.get_post_by_id(post_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{post_id}/unlike")
async def unlike_post(
        post_id: int,
        current_user: User = Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    try:
        await service.unlike_post(current_user.id, post_id)
        return service.get_post_by_id(post_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{post_id}/comment", response_model=CommentResponse)
async def comment_on_post(
        post_id: int,
        comment_data: CommentRequest,  # ✅ Ensure this matches the correct schema
        current_user: User = Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    print(f"Received comment data: {comment_data}")
    try:
        return await service.comment_on_post(current_user.id, post_id, comment_data.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.get("/posts/nutrition-statistics", response_model=MealStatisticsResponse)
def get_nutrition_statistics(
        start_date: str,
        end_date: str,
        service: SocialService = Depends(get_social_service),
        current_user=Depends(get_current_user)
):

    try:
        return service.get_user_nutrition_statistics(current_user.id, start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
