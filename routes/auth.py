# auth.py (modificat)
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app_utils.security import get_current_user, create_access_token
from services.user_service import UserService
from schemas.user import UserResponse, UserLogin
from models.user import User
from app_utils.dependencies import get_user_service

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        file: UploadFile = File(...),
        service: UserService = Depends(get_user_service)
):
    try:
        user = service.register_user(username, email, password, file)
        # if user.profile_picture and not user.profile_picture.startswith("http"):
        #     user.profile_picture = f"http://localhost:8000{user.profile_picture}"
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(user: UserLogin, service: UserService = Depends(get_user_service)):
    try:
        db_user = service.authenticate_user(user.email, user.password)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "profile_picture": db_user.profile_picture
        }
    }

@router.get("/me", response_model=UserResponse)
def get_current_logged_in_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/lookup/userid/{username}")
def get_user_id_by_username(
    username: str,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    user = service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id}

@router.get("/lookup/username/{user_id}")
def get_username_by_id(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    try:
        username = service.get_username_by_id(user_id)
        return {"username": username}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/search", response_model=list[UserResponse])
def search_users(username: str, service: UserService = Depends(get_user_service)):
    users = service.search_users(username)
    # for user in users:
    #     if user.profile_picture and not user.profile_picture.startswith("http"):
    #         user.profile_picture = f"http://localhost:8000{user.profile_picture}"
    return users
