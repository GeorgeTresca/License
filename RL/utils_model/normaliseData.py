import json
import pandas as pd

file_path = '../data/adjusted_recipes.json'
with open(file_path, 'r') as file:
    recipes = json.load(file)

df = pd.DataFrame(recipes)

df = df[['name', 'calories', 'macros', 'taste_score']]

df['protein'] = df['macros'].apply(lambda x: x['protein'])
df['fat'] = df['macros'].apply(lambda x: x['fat'])
df['carbs'] = df['macros'].apply(lambda x: x['carbs'])
df = df.drop(columns=['macros'])

meals_dataset = df[(df['calories'] >= 100) & (df['calories'] <= 1000)]

meals_dataset['normalized_calories'] = (meals_dataset['calories'] - meals_dataset['calories'].min()) / \
                                       (meals_dataset['calories'].max() - meals_dataset['calories'].min())

meals_dataset.to_csv('processed_recipes.csv', index=False)
