from pydantic import BaseModel, HttpUrl


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    profile_picture: HttpUrl


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
