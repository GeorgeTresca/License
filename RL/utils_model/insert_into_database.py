import json
from sqlalchemy.orm import Session
from database import SessionLocal
from repositories.meal_repository import MealRepository

# Load meals from JSON
JSON_FILE = "../data/adjusted_recipes_with_images.json"

with open(JSON_FILE, "r") as f:
    recipes = json.load(f)

# Open a database session
db: Session = SessionLocal()
meal_repo = MealRepository(db)

for meal in recipes:
    # Check if meal already exists by name
    existing_meal = meal_repo.get_meal_by_name(meal["name"])
    if not existing_meal:
        meal_repo.create_meal(
            name=meal["name"],
            calories=meal["calories"],
            protein=meal["macros"]["protein"],
            carbs=meal["macros"]["carbs"],
            fats=meal["macros"]["fat"],
            photo_url=meal.get("photo_url"),
            ingredients=meal["ingredients"]  # ✅ Save ingredients as JSON
        )

db.close()
print("✅ Meals successfully added to the database!")
