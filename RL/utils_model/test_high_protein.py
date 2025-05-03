import pickle
import os
import random
import json


DATASET_FILE = "../data/adjusted_recipes.json"
if not os.path.exists(DATASET_FILE):
    raise FileNotFoundError(f"Dataset file '{DATASET_FILE}' not found!")

with open(DATASET_FILE, "r") as f:
    meal_data = json.load(f)

CALORIE_RANGES = range(1200, 2601, 100)


def load_q_table():
    q_table_file = "../tables/q_table_high-protein.pkl"
    if os.path.exists(q_table_file):
        with open(q_table_file, 'rb') as f:
            return pickle.load(f)
    else:
        raise ValueError("No trained model found for high-protein.")


def filter_high_protein_meals():
    return [meal for meal in meal_data if meal["macros"]["protein"] > 25]


def recommend_meals_for_all_calories():

    q_table = load_q_table()

    high_protein_meals = filter_high_protein_meals()

    print(f"🔎 Testing all calorie levels for high-protein...")

    results = {}

    for target_calories in CALORIE_RANGES:
        if target_calories not in q_table:
            print(f"No trained Q-values for {target_calories} kcal in high-protein model")
            continue

        state = []
        current_calories = 0
        available_meals = list(range(len(high_protein_meals)))
        num_meals = 4
        recommendations = []

        for _ in range(num_meals):
            state_key = tuple(state)

            if state_key in q_table[target_calories]:
                action = max(q_table[target_calories][state_key], key=q_table[target_calories][state_key].get)
            else:
                action = random.choice(available_meals)

            meal = high_protein_meals[action]
            state.append(action)
            current_calories += meal['calories']
            available_meals.remove(action)
            recommendations.append((meal['name'], meal['calories'], meal['macros']['protein']))

        results[target_calories] = {
            "meals": recommendations,
            "total_calories": current_calories
        }

    print("=" * 60)

    for target_calories, data in results.items():
        print(f"Target Calories: {target_calories} kcal")
        for meal_name, meal_calories, meal_protein in data["meals"]:
            print(f"   - {meal_name}: {meal_calories} kcal, {meal_protein}g protein")
        print(f"   Total Calories: {data['total_calories']} kcal")
        print("-" * 60)

    return results


recommend_meals_for_all_calories()
