import json
from sqlalchemy.orm import Session
from database import SessionLocal
from repositories.meal_repository import MealRepository

# Load meals from JSON
JSON_FILE = "../RL/data/adjusted_recipes_with_images.json"

with open(JSON_FILE, "r") as f:
    recipes = json.load(f)

# Open a database session
db: Session = SessionLocal()
meal_repo = MealRepository(db)

for meal in recipes:
    # Check if meal already exists
    existing_meal = meal_repo.get_meal_by_id(meal["id"])
    if not existing_meal:
        # Save new meal
        meal_repo.create_meal(
            name=meal["name"],
            calories=meal["calories"],
            protein=meal["macros"]["protein"],
            carbs=meal["macros"]["carbs"],
            fats=meal["macros"]["fats"],
            photo_url=meal.get("photo_url")  # Default to None if not provided
        )

db.close()
print("✅ Meals successfully added to the database!")
