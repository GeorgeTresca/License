
import os
import pickle
import logging
from train_utils import train_rl_agent, load_recipes

logging.basicConfig(level=logging.INFO)

class MealPlannerEnv:
    def __init__(self, meals, target_calories):
        self.meals = meals
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
        self.available_meals.remove(action)

        done = len(self.state) == self.num_meals

        # Reward calculation for calories + protein + fat
        calorie_deviation = abs(self.current_calories - self.target_calories)
        protein_penalty = sum(
            25 - self.meals[i]['macros']['protein'] for i in self.state if self.meals[i]['macros']['protein'] < 25)

        # Fat condition: Penalize heavily if any meal exceeds 20g fat
        fat_penalty = sum(
            self.meals[i]['macros']['fat'] - 20 for i in self.state if self.meals[i]['macros']['fat'] > 20)

        reward = -(calorie_deviation + protein_penalty + fat_penalty)
        return self._get_state(), reward, done

    def get_actions(self):
        return self.available_meals

    def _get_state(self):
        return {
            'selected_meals': self.state,
            'current_calories': self.current_calories,
            'remaining_meals': self.available_meals
        }

recipes = load_recipes()

calorie_targets = range(1400, 2601, 100)
q_table_file = "../tables/q_table_calories_protein_fat.pkl"

if not os.path.exists(q_table_file):
    all_q_tables = {}

    for calorie_target in calorie_targets:
        env = MealPlannerEnv(recipes, calorie_target)
        q_table = train_rl_agent(env, episodes=200000)
        all_q_tables[calorie_target] = q_table

    with open(q_table_file, 'wb') as f:
        pickle.dump(all_q_tables, f)

    logging.info(f"✅ Model trained and saved: {q_table_file}")

logging.info("Calories + Protein + Fat training complete!")
