import pickle
import os
import random
import json

DATASET_FILE = "../data/adjusted_recipes.json"
if not os.path.exists(DATASET_FILE):
    raise FileNotFoundError(f"Dataset file '{DATASET_FILE}' not found!")

with open(DATASET_FILE, "r") as f:
    meal_data = json.load(f)

CALORIE_RANGES = range(800, 1401, 100)


def load_q_table():
    q_table_file = "../tables/q_table_vegan.pkl"
    if os.path.exists(q_table_file):
        with open(q_table_file, 'rb') as f:
            return pickle.load(f)
    else:
        raise ValueError("No trained model found for vegan.")


def filter_vegan_meals():
    banned_ingredients = {
        "bacon", "beef chunks", "beef strips", "butter", "cheddar cheese", "cheese",
        "chicken breast", "duck breast", "eggs", "fish fillet", "ground beef",
        "ground turkey", "honey", "lamb chops", "lamb chunks", "milk", "parmesan",
        "pork ribs", "pork strips", "pork tenderloin", "pulled pork", "salmon fillet",
        "shrimp", "sour cream", "steak", "trout fillet", "tuna", "tuna steak",
        "turkey breast", "turkey slices"
    }

    return [
        meal for meal in meal_data if not any(
            ingredient in banned_ingredients for ingredient in meal["ingredients"]
        )
    ]


def recommend_meals_for_all_calories():
    q_table = load_q_table()

    vegan_meals = filter_vegan_meals()

    print(f"🔎 Testing all calorie levels for vegan...")

    results = {}

    for target_calories in CALORIE_RANGES:
        if target_calories not in q_table:
            print(f"❌ No trained Q-values for {target_calories} kcal in vegan model")
            continue

        state = []
        current_calories = 0
        available_meals = list(range(len(vegan_meals)))
        num_meals = 4
        recommendations = []

        for _ in range(num_meals):
            state_key = tuple(state)

            if state_key in q_table[target_calories]:
                action = max(q_table[target_calories][state_key], key=q_table[target_calories][state_key].get)
            else:
                action = random.choice(available_meals)

            meal = vegan_meals[action]
            state.append(action)
            current_calories += meal['calories']
            available_meals.remove(action)
            recommendations.append((meal['name'], meal['calories']))

        results[target_calories] = {
            "meals": recommendations,
            "total_calories": current_calories
        }

    for target_calories, data in results.items():
        print(f"Target Calories: {target_calories} kcal")
        for meal_name, meal_calories in data["meals"]:
            print(f"   - {meal_name}: {meal_calories} kcal")
        print(f"Total Calories: {data['total_calories']} kcal")
        print("-" * 60)

    return results


recommend_meals_for_all_calories()
