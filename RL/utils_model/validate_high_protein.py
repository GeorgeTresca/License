import pickle
import os
import numpy as np
import matplotlib.pyplot as plt
import logging
from recommend_meals import recommend_meals
from RL.scripts.train_utils import MealPlannerEnv, load_recipes
from RL.utils_model.calories_config import CALORIE_RANGES

logging.basicConfig(level=logging.INFO)

# Load recipes
db_recipes = load_recipes()
calorie_targets = range(800, 2801, 100)

def calculate_achievement_ratio(selected_meals, target_calories, tolerance=100):
    total_calories = sum(meal.calories for meal in selected_meals)
    deviation = abs(total_calories - target_calories)
    success = deviation <= tolerance
    return deviation, success

def track_results():
    total_successful_cases = 0
    total_cases = 0
    deviations = []

    for calorie_target in calorie_targets:
        try:
            selected_meals = recommend_meals("high-protein", calorie_target)
            deviation, success = calculate_achievement_ratio(selected_meals, calorie_target)
            deviations.append((calorie_target, deviation))
            total_successful_cases += success
            total_cases += 1

            logging.info(f"Target: {calorie_target}, Deviation: {deviation:.2f}, Success: {'Y' if success else 'N'}")

        except ValueError:
            logging.warning(f"No trained Q-values for {calorie_target} kcal in profile 'high-protein'")
            continue

    # Achievement Ratio Calculation
    achievement_ratio = total_successful_cases / total_cases if total_cases else 0
    logging.info(f"Achievement Ratio (Calorie Deviation Successes): {achievement_ratio * 100:.2f}%")


if __name__ == "__main__":
    track_results()
