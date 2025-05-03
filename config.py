import json
import os

# Define the config file path
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# Load configuration from config.json
with open(CONFIG_PATH, "r") as config_file:
    config = json.load(config_file)

DATABASE_URL = config["DATABASE_URL"]
SECRET_KEY = config["SECRET_KEY"]
ALGORITHM = config["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = config["ACCESS_TOKEN_EXPIRE_MINUTES"]
