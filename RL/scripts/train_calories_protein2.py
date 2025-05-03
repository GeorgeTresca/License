import random
import json
import os
import os
import pickle
import logging

from RL.utils_model.calories_config import CALORIE_RANGES

DATASET_FILE = "../data/adjusted_recipes.json"


def load_recipes():
    if not os.path.exists(DATASET_FILE):
        raise FileNotFoundError(f"Dataset file '{DATASET_FILE}' not found!")

    with open(DATASET_FILE, "r") as f:
        return json.load(f)


class MealPlannerEnv:

    def __init__(self, meals, target_calories, filter_function=None):
        self.meals = filter_function(meals) if filter_function else meals
        self.target_calories = target_calories
        self.num_meals = 4
        self.state = []
        self.current_calories = 0
        self.available_meals = list(range(len(self.meals)))

    def reset(self):
        self.state = []
        self.current_calories = 0
        self.available_meals = list(range(len(self.meals)))
        return self._get_state()

    def step(self, action):
        if action not in self.available_meals:
            raise ValueError("Selected meal is not available.")

        meal = self.meals[action]
        self.state.append(action)
        self.current_calories += meal['calories']
        protein_penalty = max(0, 25 - meal['macros']['protein']) * 2

        protein_bonus = 10 if meal['macros']['protein'] >= 30 else 0

        self.available_meals.remove(action)
        done = len(self.state) == self.num_meals

        deviation = abs(self.current_calories - self.target_calories)
        if deviation <= 100:
            reward = 10
        else:
            reward = -deviation

        reward = reward - protein_penalty + protein_bonus

        return self._get_state(), reward, done

    def get_actions(self):
        return self.available_meals

    def _get_state(self):
        return {
            'selected_meals': self.state,
            'current_calories': self.current_calories,
            'remaining_meals': self.available_meals
        }


def train_rl_agent(env, episodes=200000, epsilon=0.1, alpha=0.1):
    q_table = {}

    for episode in range(episodes):
        state = env.reset()
        state_key = tuple(state['selected_meals'])

        if state_key not in q_table:
            q_table[state_key] = {action: 0 for action in env.get_actions()}

        done = False
        while not done:
            if random.uniform(0, 1) < epsilon:
                action = random.choice(env.get_actions())
            else:
                action = max(q_table[state_key], key=q_table[state_key].get)

            next_state, reward, done = env.step(action)
            next_state_key = tuple(next_state['selected_meals'])

            if next_state_key not in q_table:
                q_table[next_state_key] = {action: 0 for action in env.get_actions()}

            old_value = q_table[state_key][action]
            next_max = max(q_table[next_state_key].values())

            q_table[state_key][action] = old_value + alpha * (reward + next_max - old_value)
            state_key = next_state_key

    return q_table



recipes = load_recipes()

calorie_targets = CALORIE_RANGES["high-protein"]

q_table_file = "../tables/q_table_high-protein3.pkl"

if not os.path.exists(q_table_file):
    all_q_tables = {}

    for calorie_target in calorie_targets:
        env = MealPlannerEnv(recipes, calorie_target)
        q_table = train_rl_agent(env, episodes=200000)
        all_q_tables[calorie_target] = q_table

    with open(q_table_file, 'wb') as f:
        pickle.dump(all_q_tables, f)

    logging.info(f"✅ Model trained and saved: {q_table_file}")

logging.info("High-protein training complete!")
