from fastapi import APIRouter, Depends, HTTPException
from schemas.meal_recommendation import MealRecommendationResponse
from services.meal_service import MealService
from app_utils.security import get_current_user
from app_utils.dependencies import get_meal_service

router = APIRouter()


@router.get("/recommendations", response_model=MealRecommendationResponse)
def get_meal_recommendations(
        profile: str,
        target_calories: int,
        service: MealService = Depends(get_meal_service),
        current_user=Depends(get_current_user)
):
    try:
        return service.get_meal_recommendations(current_user.id, profile, target_calories)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/saved-recommendations", response_model=list[MealRecommendationResponse])
def get_user_meal_recommendations(
        service: MealService = Depends(get_meal_service),
        current_user=Depends(get_current_user)
):
    return service.get_user_meal_recommendations(current_user.id)


@router.delete("/saved-recommendations/{recommendation_id}")
def delete_meal_recommendation(
        recommendation_id: int,
        service: MealService = Depends(get_meal_service),
        current_user=Depends(get_current_user)
):
    try:
        return service.delete_meal_recommendation(current_user.id, recommendation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
