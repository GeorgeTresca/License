########## TEST MODEL FOR THE 1200-2600 CALORIE RANGE, APPROACHING THE USER INPUT TO THE CLOSEST Q TABLE



import pickle
import pandas as pd

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
        return self._get_state(), 0, done

    def get_actions(self):
        return self.available_meals

def recommend_meals(q_table, env):
    state = env.reset()
    done = False
    recommendations = []
    total_calories = 0

    while not done:
        state_key = tuple(state['selected_meals'])

        if state_key not in q_table:
            break

        action = max(q_table[state_key], key=q_table[state_key].get)
        state, _, done = env.step(action)
        meal = env.meals[action]
        recommendations.append((meal['name'], meal['calories']))
        total_calories += meal['calories']

    return recommendations, total_calories

q_table_file = '../tables/q_table_1200_2600_100pkl'
with open(q_table_file, 'rb') as f:
    all_q_tables = pickle.load(f)

filtered_df = pd.read_csv('../scripts/processed_recipes.csv')
processed_meals = filtered_df.to_dict('records')

while True:
    try:
        user_input = input("Enter your desired calorie target (1200-2600, or 'exit' to quit): ")
        if user_input.lower() == 'exit':
            print("Exiting the program. Goodbye!")
            break

        target_calories = int(user_input)
        if target_calories < 1200 or target_calories > 2600:
            print("Please enter a value between 1200 and 2600.")
            continue

        closest_target = min(all_q_tables.keys(), key=lambda x: abs(x - target_calories))
        print(f"Using Q-table for closest target calories: {closest_target}")

        env = MealPlannerEnv(processed_meals, closest_target)
        q_table = all_q_tables[closest_target]
        recommendations, total_calories = recommend_meals(q_table, env)

        print("Recommended meals and calories:")
        for meal_name, calories in recommendations:
            print(f"- {meal_name}: {calories} kcal")
        print(f"Total calories: {total_calories} kcal\n")

    except ValueError:
        print("Invalid input. Please enter a numeric value or 'exit'.")
