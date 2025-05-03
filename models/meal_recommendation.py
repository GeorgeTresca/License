from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from database import Base

class MealRecommendation(Base):
    __tablename__ = "meal_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    profile_type = Column(String, nullable=False)
    target_calories = Column(Integer, nullable=False)

    meals = relationship("Meal", secondary="recommendation_meal_association")
