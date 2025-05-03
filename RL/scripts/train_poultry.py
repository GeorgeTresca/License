import os
import pickle
import logging

from train_utils import train_rl_agent, MealPlannerEnv, load_recipes
from RL.utils_model.calories_config import CALORIE_RANGES


logging.basicConfig(level=logging.INFO)


recipes = load_recipes()


calorie_targets = CALORIE_RANGES["poultry"]


def filter_poultry(meals):
    banned_ingredients = {
        "beef chunks", "beef strips", "pork ribs", "pork strips", "pork tenderloin",
        "lamb chops", "lamb chunks", "fish fillet", "salmon fillet", "shrimp",
        "trout fillet", "tuna", "tuna steak", "ground beef", "pulled pork", "bacon", "steak"
    }
    return [
        meal for meal in meals if not any(
            ingredient in banned_ingredients for ingredient in meal["ingredients"]
        )
    ]


q_table_file = "../tables/q_table_poultry.pkl"


if not os.path.exists(q_table_file):
    all_q_tables = {}

    for calorie_target in calorie_targets:
        env = MealPlannerEnv(recipes, calorie_target, filter_poultry)
        q_table = train_rl_agent(env, episodes=200000)
        all_q_tables[calorie_target] = q_table

    with open(q_table_file, 'wb') as f:
        pickle.dump(all_q_tables, f)

    logging.info(f"Model trained and saved: {q_table_file}")

