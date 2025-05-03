###### IMPLEMENTED THE TRAINING FOR 1200-2600 CALORIE RANGE, PRECISE, 100 TO 100 RANGE
#epsilon =0.1

import random
from train_utils import train_rl_agent
import pickle
import os
from RL.utils_model.normaliseData import meals_dataset


class MealPlannerEnv:
    def __init__(self, meals, target_calories):
        self.meals = meals
        self.target_calories = target_calories
        self.num_meals = 4
        self.state = []
        self.current_calories = 0
        self.available_meals = list(range(len(meals)))

    def reset(self):
        self.state = []
        self.current_calories = 0
        self.available_meals = list(range(len(self.meals)))
        return self._get_state()

    def _get_state(self):
        return {
            'selected_meals': self.state,
            'current_calories': self.current_calories,
            'remaining_meals': self.available_meals
        }

    def step(self, action):
        if action not in self.available_meals:
            raise ValueError("Selected meal is not available.")

        meal = self.meals[action]
        self.state.append(action)
        self.current_calories += meal['calories']
        self.available_meals.remove(action)

        done = len(self.state) == self.num_meals

        if done:
            deviation = abs(self.current_calories - self.target_calories)
            reward = -deviation if deviation <= 100 else -deviation * 2
        else:
            reward = 0

        return self._get_state(), reward, done

    def get_actions(self):
        return self.available_meals


processed_meals = meals_dataset.to_dict('records')

meals_dataset.loc[:, 'normalized_calories'] = (meals_dataset['calories'] - meals_dataset['calories'].min()
                                               ) / (meals_dataset['calories'].max() - meals_dataset['calories'].min())

q_table_path = '../tables/q_table_1200_2600_100pkl'
if not os.path.exists(q_table_path):
    all_q_tables = {}
    for target_calories in range(1200, 2601, 100):
        env = MealPlannerEnv(processed_meals, target_calories)
        q_table = train_rl_agent(env, episodes=200000)
        all_q_tables[target_calories] = q_table

    with open(q_table_path, 'wb') as f:
        pickle.dump(all_q_tables, f)
else:
    with open(q_table_path, 'rb') as f:
        all_q_tables = pickle.load(f)



