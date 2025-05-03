import json
import os
import glob


INPUT_FILE = "../data/adjusted_recipes.json"
OUTPUT_FILE = "../data/adjusted_recipes_with_images.json"
IMAGE_FOLDER = "../recipe_images"


def find_image(recipe_name):
    formatted_name = recipe_name.replace(" ", "_")
    search_pattern = os.path.join(IMAGE_FOLDER, formatted_name) + ".*"

    image_files = glob.glob(search_pattern)
    if image_files:
        return image_files[0].replace("\\", "/")
    return None


def attach_image_paths():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        recipes = json.load(file)

    for recipe in recipes:
        image_path = find_image(recipe["name"])
        recipe["photo_url"] = image_path if image_path else "recipe_images/default.jpg"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(recipes, file, indent=4)

    print(f"✅ Updated recipes saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    attach_image_paths()
