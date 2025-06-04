import json

normalization_map = {
    # Chicken
    "chicken thighs": "chicken breast",
    "chicken drumsticks": "chicken breast",
    "chicken meat": "chicken breast",
    "chicken tenders": "chicken breast",

    # Rice
    "white rice": "basmati rice",
    "brown rice": "basmati rice",
    "wild rice": "basmati rice",
    "jasmine rice": "basmati rice",
    "arborio rice": "basmati rice",

    # Pasta
    "spaghetti": "pasta",
    "fettuccine": "pasta",
    "linguine": "pasta",
    "macaroni": "pasta",
    "lasagna noodles": "pasta",
    "penne": "pasta",
    "farfalle": "pasta",
    "rotini": "pasta",
    "rigatoni": "pasta",
    "pasta shells": "pasta",
    "egg noodles": "noodles",

    # Fish fillet
    "salmon fillet": "fish fillet",
    "tilapia fillet": "fish fillet",
    "cod fillet": "fish fillet",
    "tron fillet": "fish fillet",

    # Cheese
    "mozzarella cheese": "cheese",
    "parmesan cheese": "cheese",
    "ricotta cheese": "cheese",
    "cheddar cheese": "cheese",
    "feta cheese": "cheese",

    # Bread
    "white bread": "whole grain bread",
    "ciabatta bread": "whole grain bread",
    "burger bun": "burger buns",

    # Beans
    "black beans": "beans",
    "red beans": "beans",
    "kidney beans": "beans",

    # Vegetables
    "romaine lettuce": "lettuce",
    "portobello mushrooms": "mushrooms",
    "tomato": "tomatoes",
    "sweet potato": "sweet potatoes",
    "tomato paste": "tomato sauce",

    # Spices
    "curry paste": "curry",
    "basil leaves": "basil",
    "lemon": "lemon juice",
    "chili flakes": "chilli powder",
    "curry powder": "curry",

    # Others
    "egg": "eggs",

}

file_path = "../data/recipes.json"
with open(file_path, 'r') as file:
    recipes = json.load(file)

for recipe in recipes:
    normalized_ingredients = []
    for ingredient in recipe["ingredients"]:
        normalized_ingredients.append(normalization_map.get(ingredient, ingredient))
    recipe["ingredients"] = normalized_ingredients

output_path = "../../RLPlanner/data/recipes.json"
with open(output_path, 'w') as file:
    json.dump(recipes, file, indent=4)

