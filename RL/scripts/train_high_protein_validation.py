import os
import pickle
import logging

from train_utils import train_rl_agent, MealPlannerEnv, load_recipes
from RL.utils_model.calories_config import CALORIE_RANGES


logging.basicConfig(level=logging.INFO)

recipes = load_recipes()

calorie_targets = range(800,2801,100)


def filter_high_protein(meals):
    return [meal for meal in meals if meal["macros"]["protein"] > 25]


q_table_file = "../tables/q_table_high-protein_validation.pkl"

if not os.path.exists(q_table_file):
    all_q_tables = {}

    for calorie_target in calorie_targets:
        env = MealPlannerEnv(recipes, calorie_target, filter_high_protein)
        q_table = train_rl_agent(env, episodes=200000)
        all_q_tables[calorie_target] = q_table

    with open(q_table_file, 'wb') as f:
        pickle.dump(all_q_tables, f)

    logging.info(f"✅ Model trained and saved: {q_table_file}")

logging.info("High-protein training complete!")
