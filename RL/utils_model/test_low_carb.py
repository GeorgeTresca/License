import pickle
import os
import random
import json


DATASET_FILE = "../data/adjusted_recipes.json"
if not os.path.exists(DATASET_FILE):
    raise FileNotFoundError(f"Dataset file '{DATASET_FILE}' not found!")

with open(DATASET_FILE, "r") as f:
    meal_data = json.load(f)

CALORIE_RANGES = range(1000, 1501, 100)


def load_q_table():
    q_table_file = "../tables/q_table_low-carb.pkl"
    if os.path.exists(q_table_file):
        with open(q_table_file, 'rb') as f:
            return pickle.load(f)
    else:
        raise ValueError("No trained model found for low-carb.")


def filter_low_carb_meals():
    return [meal for meal in meal_data if meal["macros"]["carbs"] < 40]


def recommend_meals_for_all_calories():
    q_table = load_q_table()

    low_carb_meals = filter_low_carb_meals()

    print(f"Testing all calorie levels for low-carb...")

    results = {}

    for target_calories in CALORIE_RANGES:
        if target_calories not in q_table:
            print(f"No trained Q-values for {target_calories} kcal in low-carb model")
            continue

        state = []
        current_calories = 0
        available_meals = list(range(len(low_carb_meals)))
        num_meals = 4
        recommendations = []

        for _ in range(num_meals):
            state_key = tuple(state)

            if state_key in q_table[target_calories]:
                action = max(q_table[target_calories][state_key], key=q_table[target_calories][state_key].get)
            else:
                action = random.choice(available_meals)

            meal = low_carb_meals[action]
            state.append(action)
            current_calories += meal['calories']
            available_meals.remove(action)
            recommendations.append((meal['name'], meal['calories'], meal['macros']['carbs']))

        results[target_calories] = {
            "meals": recommendations,
            "total_calories": current_calories
        }



    for target_calories, data in results.items():
        print(f"Target Calories: {target_calories} kcal")
        for meal_name, meal_calories, meal_carbs in data["meals"]:
            print(f"   - {meal_name}: {meal_calories} kcal, {meal_carbs}g carbs")
        print(f"Total Calories: {data['total_calories']} kcal")
        print("-" * 60)

    return results


recommend_meals_for_all_calories()
