from pydantic import BaseModel


class LikeResponse(BaseModel):

    id: int
    user_id: int
    post_id: int

    class Config:
        orm_mode = True
