# services/meal_service.py
import json
from sqlalchemy.orm import Session
from RL.utils_model.calories_config import CALORIE_RANGES
from RL.utils_model.recommend_meals import recommend_meals
from schemas.meal import MealResponse
from schemas.meal_recommendation import MealRecommendationResponse

class MealService:
    def __init__(self, meal_repo, meal_recommendation_repo):
        self.meal_repo = meal_repo
        self.meal_recommendation_repo = meal_recommendation_repo

    def get_meal_recommendations(self, user_id: int, profile: str, target_calories: int) -> MealRecommendationResponse:
        if profile not in CALORIE_RANGES:
            raise ValueError(f"Invalid profile '{profile}'. Allowed: {list(CALORIE_RANGES.keys())}")
        if target_calories not in CALORIE_RANGES[profile]:
            raise ValueError(f"Invalid calorie target '{target_calories}' for {profile}. "
                             f"Allowed: {list(CALORIE_RANGES[profile])}")

        recommended_meals = recommend_meals(profile, target_calories)
        if not recommended_meals:
            raise ValueError(f"No recommendations available for {profile} at {target_calories} kcal.")

        meal_ids = [meal.id for meal in recommended_meals]
        saved = self.meal_recommendation_repo.create_recommendation(user_id, profile, target_calories, meal_ids)

        return MealRecommendationResponse(
            id=saved.id,
            user_id=saved.user_id,
            profile_type=saved.profile_type,
            target_calories=saved.target_calories,
            meals=[self._serialize_meal(m) for m in saved.meals]
        )

    def save_meal_recommendation(self, user_id: int, profile_type: str, target_calories: int, meal_ids: list[int]):
        return self.meal_recommendation_repo.create_recommendation(user_id, profile_type, target_calories, meal_ids)

    def get_user_meal_recommendations(self, user_id: int):
        recommendations = self.meal_recommendation_repo.get_user_recommendations(user_id)
        return [
            MealRecommendationResponse(
                id=rec.id,
                user_id=rec.user_id,
                profile_type=rec.profile_type,
                target_calories=rec.target_calories,
                meals=[self._serialize_meal(m) for m in rec.meals]
            )
            for rec in recommendations
        ]

    def delete_meal_recommendation(self, user_id: int, recommendation_id: int):
        deleted = self.meal_recommendation_repo.delete_recommendation(user_id, recommendation_id)
        if not deleted:
            raise ValueError(f"Meal recommendation with ID {recommendation_id} not found for user {user_id}.")
        return {"message": "Meal recommendation deleted successfully"}

    def _serialize_meal(self, meal):
        return MealResponse(
            id=meal.id,
            name=meal.name,
            calories=meal.calories,
            protein=meal.protein,
            carbs=meal.carbs,
            fats=meal.fats,
            photo_url=meal.photo_url,
            ingredients=json.loads(meal.ingredients) if isinstance(meal.ingredients, str) else meal.ingredients
        )
