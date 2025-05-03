import os
import pickle
import random
import json
import matplotlib.pyplot as plt
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
        self.available_meals.remove(action)

        done = len(self.state) == self.num_meals
        deviation = abs(self.current_calories - self.target_calories)

        # 🔥 Reward mai sensibil
        if deviation < 50:
            reward = 100 - deviation
        elif deviation < 150:
            reward = -deviation
        else:
            reward = -2 * deviation

        return self._get_state(), reward, done

    def get_actions(self):
        return self.available_meals

    def _get_state(self):
        return {
            'selected_meals': self.state,
            'current_calories': self.current_calories,
            'remaining_meals': self.available_meals
        }

def train_with_metrics(env, episodes=200000, epsilon=0.1, alpha=0.1, log_interval=1000):
    q_table = {}
    reward_log, calorie_dev_log, protein_log = [], [], []

    for episode in range(1, episodes + 1):
        state = env.reset()
        state_key = tuple(state['selected_meals'])

        if state_key not in q_table:
            q_table[state_key] = {action: 0 for action in env.get_actions()}

        done = False
        total_reward = 0
        while not done:
            if random.uniform(0, 1) < epsilon:
                action = random.choice(env.get_actions())
            else:
                action = max(q_table[state_key], key=q_table[state_key].get)
            next_state, reward, done = env.step(action)
            total_reward += reward
            next_state_key = tuple(next_state['selected_meals'])

            if next_state_key not in q_table:
                q_table[next_state_key] = {action: 0 for action in env.get_actions()}

            old_value = q_table[state_key][action]
            next_max = max(q_table[next_state_key].values(), default=0)
            q_table[state_key][action] = old_value + alpha * (reward + next_max - old_value)
            state_key = next_state_key

        if episode % log_interval == 0:
            total_protein = sum([env.meals[i]['macros']['protein'] for i in env.state])
            calorie_dev = abs(env.current_calories - env.target_calories)
            reward_log.append(total_reward)
            calorie_dev_log.append(calorie_dev)
            protein_log.append(total_protein)
            print(f"[Ep {episode}] Reward: {total_reward:.2f}, Calorie Dev: {calorie_dev}, Protein: {total_protein}g")

    return q_table, reward_log, calorie_dev_log, protein_log


# ========== Main ==========
def filter_high_protein(meals):
    return [meal for meal in meals if meal["macros"]["protein"] > 25]

def main():
    recipes = load_recipes()
    targets = CALORIE_RANGES["high-protein"]
    q_tables = {}

    reward_metrics = {}
    calorie_dev_metrics = {}
    protein_metrics = {}

    for target in targets:
        print(f"\n🚀 Training for {target} kcal...")
        env = MealPlannerEnv(recipes, target, filter_high_protein)
        q_table, rewards, deviations, proteins = train_with_metrics(env)

        q_tables[target] = q_table
        reward_metrics[target] = rewards
        calorie_dev_metrics[target] = deviations
        protein_metrics[target] = proteins

    # Save Q-tables
    with open("q_tables_high_protein2.pkl", "wb") as f:
        pickle.dump(q_tables, f)


if __name__ == "__main__":
    main()
