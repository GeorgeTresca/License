from pydantic import BaseModel, HttpUrl
from typing import List


class MealResponse(BaseModel):
    id: int
    name: str
    calories: int
    protein: float
    carbs: float
    fats: float
    photo_url: HttpUrl
    ingredients: List[str]

    class Config:
        orm_mode = True
