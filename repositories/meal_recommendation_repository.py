from sqlalchemy.orm import Session
from models.meal_recommendation import MealRecommendation
from models.meal import Meal
from models.recommendation_meal_association import recommendation_meal_association


class MealRecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_recommendation(self, user_id: int, profile_type: str, target_calories: int, meal_ids: list[int]):
        meals = self.db.query(Meal).filter(Meal.id.in_(meal_ids)).all()
        if len(meals) != len(meal_ids):
            raise ValueError("Some meal IDs are invalid.")

        new_recommendation = MealRecommendation(
            user_id=user_id,
            profile_type=profile_type,
            target_calories=target_calories,
            meals=meals
        )
        self.db.add(new_recommendation)
        self.db.commit()
        self.db.refresh(new_recommendation)
        return new_recommendation

    def get_user_recommendations(self, user_id: int):
        return self.db.query(MealRecommendation).filter(MealRecommendation.user_id == user_id).all()

    def delete_recommendation(self, user_id: int, recommendation_id: int):
        recommendation = self.db.query(MealRecommendation).filter(
            MealRecommendation.id == recommendation_id,
            MealRecommendation.user_id == user_id
        ).first()

        if not recommendation:
            return None  # No recommendation found

        self.db.delete(recommendation)
        self.db.commit()
        return recommendation
