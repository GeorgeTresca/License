import os
import pickle
import logging

from train_utils import train_rl_agent, MealPlannerEnv, load_recipes
from RL.utils_model.calories_config import CALORIE_RANGES


logging.basicConfig(level=logging.INFO)

recipes = load_recipes()

calorie_targets = CALORIE_RANGES["low-carb"]


def filter_low_carb(meals):
    return [meal for meal in meals if meal["macros"]["carbs"] < 40]


q_table_file = "../tables/q_table_low_carb.pkl"

if not os.path.exists(q_table_file):
    all_q_tables = {}

    for calorie_target in calorie_targets:
        env = MealPlannerEnv(recipes, calorie_target, filter_low_carb)
        q_table = train_rl_agent(env, episodes=200000)
        all_q_tables[calorie_target] = q_table

    with open(q_table_file, 'wb') as f:
        pickle.dump(all_q_tables, f)

    logging.info(f"✅ Model trained and saved: {q_table_file}")

logging.info("Low-carb training complete!")
