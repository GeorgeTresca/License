import json

from sqlalchemy.orm import Session
from models.meal import Meal


class MealRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_meal_by_id(self, meal_id: int):
        return self.db.query(Meal).filter(Meal.id == meal_id).first()

    def get_meals_by_ids(self, meal_ids: list[int]):
        return self.db.query(Meal).filter(Meal.id.in_(meal_ids)).all()

    def create_meal(self, name: str, calories: int, protein: float, carbs: float, fats: float, photo_url: str, ingredients: list):
        new_meal = Meal(
            name=name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fats=fats,
            photo_url=photo_url,
            ingredients=json.dumps(ingredients)
        )
        self.db.add(new_meal)
        self.db.commit()
        self.db.refresh(new_meal)
        return new_meal

    def get_meal_by_name(self, param):
        return self.db.query(Meal).filter(Meal.name == param).first()

