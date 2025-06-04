import pickle
import os
import random
import time
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models.meal import Meal
from repositories.meal_repository import MealRepository


class RLMealRecommender:
    PROFILE_FILTERS = {
        "vegan": {
            "banned": {
                "bacon", "beef chunks", "beef strips", "butter", "cheddar cheese", "cheese",
                "chicken breast", "duck breast", "eggs", "fish fillet", "ground beef",
                "ground turkey", "honey", "lamb chops", "lamb chunks", "milk", "parmesan",
                "pork ribs", "pork strips", "pork tenderloin", "pulled pork", "salmon fillet",
                "shrimp", "sour cream", "steak", "trout fillet", "tuna", "tuna steak",
                "turkey breast", "turkey slices"
            }
        },
        "high-protein": {"filter": lambda meal: meal.protein > 25},
        "low-carb": {"filter": lambda meal: meal.carbs < 40},
        "pescatarian": {
            "banned": {
                "beef chunks", "beef strips", "pork ribs", "pork strips", "pork tenderloin",
                "lamb chops", "lamb chunks", "chicken breast", "duck breast", "turkey breast",
                "turkey slices", "bacon", "ground beef", "ground turkey", "pulled pork", "steak"
            }
        },
        "poultry": {
            "banned": {
                "beef chunks", "beef strips", "pork ribs", "pork strips", "pork tenderloin",
                "lamb chops", "lamb chunks", "fish fillet", "salmon fillet", "shrimp",
                "trout fillet", "tuna", "tuna steak", "ground beef", "pulled pork", "bacon", "steak"
            }
        },
        "omnivore": {},
    }

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.q_tables_dir = os.path.join(base_dir, "tables")
        self.db: Session = SessionLocal()
        self.meal_repo = MealRepository(self.db)

    def load_q_table(self, profile):
        q_table_file = os.path.join(self.q_tables_dir, f"q_table_{profile}.pkl")
        if not os.path.exists(q_table_file):
            raise ValueError(f"No trained model found for profile '{profile}' at {q_table_file}")
        with open(q_table_file, 'rb') as f:
            return pickle.load(f)

    def filter_meals(self, profile):
        all_meals = self.meal_repo.get_meals_by_ids(
            [meal.id for meal in self.db.query(Meal).all()]
        )

        if "banned" in self.PROFILE_FILTERS[profile]:
            banned = self.PROFILE_FILTERS[profile]["banned"]
            return [meal for meal in all_meals if not any(
                ingredient in banned for ingredient in json.loads(meal.ingredients)
            )]
        elif "filter" in self.PROFILE_FILTERS[profile]:
            return [meal for meal in all_meals if self.PROFILE_FILTERS[profile]["filter"](meal)]
        return all_meals

    def recommend(self, profile, target_calories):
        q_table = self.load_q_table(profile)
        filtered_meals = self.filter_meals(profile)

        if target_calories not in q_table:
            raise ValueError(f"No trained Q-values for {target_calories} kcal in profile '{profile}'")

        state = []
        available_meals = list(range(len(filtered_meals)))
        recommendations = []

        for _ in range(4):
            state_key = tuple(state)
            if state_key in q_table[target_calories]:
                action = max(q_table[target_calories][state_key], key=q_table[target_calories][state_key].get)
            else:
                action = random.choice(available_meals)

            meal = filtered_meals[action]
            state.append(action)
            available_meals.remove(action)
            recommendations.append(meal)

        return recommendations

    def test_speed_and_output(self, profile, target_calories):
        start_time = time.time()
        try:
            recommendations = self.recommend(profile, target_calories)
            end_time = time.time()
            print(f"⏱️ Recommendation for {profile} ({target_calories} kcal) took {end_time - start_time:.4f} seconds.")
            total_calories = sum(meal.calories for meal in recommendations)
            for meal in recommendations:
                print(f"🍽️ {meal.name} - {meal.calories} kcal - {meal.protein}g protein")
            print(f"Total calories: {total_calories}")
        except ValueError as e:
            print(f" {e}")


# Externally exposed function (to keep API and service code unchanged)
_recommender = RLMealRecommender()


def recommend_meals(profile, target_calories):
    return _recommender.recommend(profile, target_calories)


if __name__ == "__main__":
    for i in range(1500, 2001, 100):
        _recommender.test_speed_and_output("omnivore", i)
