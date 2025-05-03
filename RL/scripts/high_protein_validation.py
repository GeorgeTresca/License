import pickle
import os
import numpy as np
import logging

from RL.utils_model.recommend_meals import recommend_meals
from train_utils import MealPlannerEnv, load_recipes
from RL.utils_model.calories_config import CALORIE_RANGES

logging.basicConfig(level=logging.INFO)

# Load recipes
db_recipes = load_recipes()
calorie_targets = range(1400, 2601, 100)

def calculate_achievement_ratio(selected_meals, target_calories, tolerance=100):
    total_calories = sum(meal.calories for meal in selected_meals)
    deviation = abs(total_calories - target_calories)
    success = deviation <= tolerance
    return deviation, success

def track_variance(trials=10):
    calorie_deviation_data = {target: [] for target in calorie_targets}
    total_successful_cases = 0
    total_cases = 0

    for calorie_target in calorie_targets:
        successful_cases = 0
        deviations = []

        for _ in range(trials):
            try:
                selected_meals = recommend_meals("high-protein", calorie_target)
                deviation, success = calculate_achievement_ratio(selected_meals, calorie_target)
                deviations.append(deviation)
                successful_cases += success
            except ValueError:
                logging.warning(f"No trained Q-values for {calorie_target} kcal in profile 'high-protein'")
                continue

        if deviations:
            calorie_deviation_data[calorie_target] = deviations
            total_successful_cases += successful_cases
            total_cases += trials

        avg_deviation = np.mean(deviations) if deviations else 0
        variance = np.var(deviations) if deviations else 0

        logging.info(f"Target: {calorie_target}, Avg Deviation: {avg_deviation:.2f}, Variance: {variance:.2f}, Success Rate: {successful_cases/trials:.2%}")

    # Achievement Ratio Calculation
    achievement_ratio = total_successful_cases / total_cases if total_cases else 0
    logging.info(f"Achievement Ratio (Calorie Deviation Successes): {achievement_ratio * 100:.2f}%")

if __name__ == "__main__":
    track_variance(trials=100)
