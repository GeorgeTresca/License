from pydantic import BaseModel
from typing import List
from schemas.meal import MealResponse


class MealRecommendationResponse(BaseModel):
    id: int
    user_id: int
    profile_type: str
    target_calories: int
    meals: List[MealResponse]

    class Config:
        orm_mode = True
