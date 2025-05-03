import json

file_path = "../../RLPlanner/data/recipes.json"
with open(file_path, 'r') as file:
    recipes = json.load(file)

for recipe in recipes:
    protein = recipe["macros"]["protein"]
    carbs = recipe["macros"]["carbs"]
    fat = recipe["macros"]["fat"]
    recipe["calories"] = 4 * protein + 4 * carbs + 9 * fat

output_path = "../../RLPlanner/data/recipes.json"
with open(output_path, 'w') as file:
    json.dump(recipes, file, indent=4)

