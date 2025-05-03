from sqlalchemy import Column, Integer, String, Float, Text
from database import Base


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    ingredients = Column(Text, nullable=False)
    photo_url = Column(String, nullable=True)
