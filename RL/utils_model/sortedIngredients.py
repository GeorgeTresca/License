import json

file_path = "../data/adjusted_recipes.json"
with open(file_path, 'r') as file:
    recipes = json.load(file)

unique_ingredients = set()
for recipe in recipes:
    unique_ingredients.update(recipe["ingredients"])

sorted_ingredients = sorted(unique_ingredients)

output_path = "../data/sorted_ingredients.txt"
with open(output_path, 'w') as file:
    file.write("\n".join(sorted_ingredients))

print(f"\nSorted ingredients have been saved to {output_path}")


