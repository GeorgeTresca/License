import pickle
import os
import random
import time
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models.meal import Meal
from repositories.meal_repository import MealRepository

db: Session = SessionLocal()
meal_repo = MealRepository(db)

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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q_TABLES_DIR = os.path.join(BASE_DIR, "tables")


def load_q_table(profile):
    q_table_file = os.path.join(Q_TABLES_DIR, f"q_table_{profile}.pkl")
    # q_table_file = os.path.join(Q_TABLES_DIR, f"q_table_high-protein5.pkl")

    if not os.path.exists(q_table_file):
        raise ValueError(f"No trained model found for profile '{profile}' at {q_table_file}")

    with open(q_table_file, 'rb') as f:
        return pickle.load(f)


def filter_meals(profile):
    """Retrieve meals from the database and filter based on profile."""
    all_meals = meal_repo.get_meals_by_ids([meal.id for meal in db.query(Meal).all()])

    if "banned" in PROFILE_FILTERS[profile]:
        banned_ingredients = PROFILE_FILTERS[profile]["banned"]
        return [
            meal for meal in all_meals if not any(
                ingredient in banned_ingredients for ingredient in json.loads(meal.ingredients)
            )
        ]
    elif "filter" in PROFILE_FILTERS[profile]:
        return [meal for meal in all_meals if PROFILE_FILTERS[profile]["filter"](meal)]
    return all_meals


def recommend_meals(profile, target_calories):
    q_table = load_q_table(profile)
    filtered_meals = filter_meals(profile)

    if target_calories not in q_table:
        raise ValueError(f"No trained Q-values for {target_calories} kcal in profile '{profile}'")

    state = []
    available_meals = list(range(len(filtered_meals)))
    num_meals = 4
    recommendations = []

    for _ in range(num_meals):
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


def test_speed_and_output(profile, target_calories):
    start_time = time.time()
    try:
        recommendations = recommend_meals(profile, target_calories)
        end_time = time.time()
        print(f"⏱️ Recommendation for {profile} ({target_calories} kcal) took {end_time - start_time:.4f} seconds.")
        total_calories = 0
        for meal in recommendations:
            print(f"🍽️ {meal.name} - {meal.calories} kcal - {meal.protein}g protein")
            total_calories += meal.calories
        print(f"Total calories: {total_calories}")
    except ValueError as e:
        print(f" {e}")

if __name__ == "__main__":
    for i in range(1000,1501,100):
        test_speed_and_output("low-carb", i)



