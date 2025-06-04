from pydantic import BaseModel, HttpUrl, validator, field_validator
from typing import Optional, Any

BASE_URL = "http://localhost:8000"

class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    profile_picture: HttpUrl

    @field_validator("profile_picture", mode="before")
    @classmethod
    def create_full_url(cls, value: Any) -> Any:
        if value and isinstance(value, str) and not value.startswith("http"):
            return f"{BASE_URL}{value}"
        return value


