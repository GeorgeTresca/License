from pydantic import BaseModel
from datetime import datetime


class CommentResponse(BaseModel):
    id: int
    user_id: int
    username: str
    post_id: int
    text: str
    created_at: datetime

    class Config:
        orm_mode = True


class CommentRequest(BaseModel):
    text: str
