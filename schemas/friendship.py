from pydantic import BaseModel
from datetime import datetime

class FriendRequest(BaseModel):
    receiver_id: int

class FriendResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime
