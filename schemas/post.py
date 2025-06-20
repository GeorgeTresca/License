from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict
from datetime import datetime
from typing import List

from schemas.comment import CommentResponse
from schemas.like import LikeResponse




class PostResponse(BaseModel):
    id: int
    user_id: int
    username: str
    caption: Optional[str]
    image_url: HttpUrl
    macros: Optional[Dict[str, float]]
    created_at: datetime
    likes: List[LikeResponse] = []  # ✅ Include like details
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True


class MealStatisticsResponse(BaseModel):
    average_calories: float
    average_protein: float
    average_carbs: float
    average_fats: float
    protein_distribution: float
    carbs_distribution: float
    fats_distribution: float
    total_days_considered: int

    class Config:
        from_attributes = True
