from logging.config import fileConfig
import json
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

# Load config.json manually (since we don't use .env)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(CONFIG_PATH, "r") as config_file:
    config_data = json.load(config_file)

DATABASE_URL = config_data["DATABASE_URL"]

# Import your Base metadata (ensure this path is correct)
from database import Base  # Update this path if needed
from models.user import User
from models.friendship import Friendship
from models.post import Post
from models.like import Like
from models.comment import Comment
from models.meal import Meal
from models.meal_recommendation import MealRecommendation
from models.recommendation_meal_association import recommendation_meal_association
# from app.models.saved_meal import SavedMeal
# from app.models.comment import Comment
# from models.like import Like

target_metadata = Base.metadata


# This tells Alembic what database schema to manage
target_metadata = Base.metadata

# Alembic Config object
config = context.config

# Override sqlalchemy.url in Alembic with the DATABASE_URL from config.json
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
