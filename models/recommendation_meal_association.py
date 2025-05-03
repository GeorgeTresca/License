from sqlalchemy import Table, Column, Integer, ForeignKey
from database import Base

recommendation_meal_association = Table(
    "recommendation_meal_association",
    Base.metadata,
    Column("recommendation_id", Integer, ForeignKey("meal_recommendations.id")),
    Column("meal_id", Integer, ForeignKey("meals.id")),
)
