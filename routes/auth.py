from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app_utils.dependencies import get_social_service
from models.user import User
from schemas.user import UserResponse, UserLogin
from app_utils.security import get_current_user, create_access_token
from services.social_service import SocialService, BASE_URL

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(
        username: str = Form(...),  # ✅ Data from FormData
        email: str = Form(...),  # ✅ Data from FormData
        password: str = Form(...),  # ✅ Data from FormData
        file: UploadFile = File(...),  # ✅ File Upload
        service: SocialService = Depends(get_social_service)
):
    try:
        new_user = service.register_user(username, email, password, file)
        if not new_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return new_user


@router.post("/login")
def login(user: UserLogin, service: SocialService = Depends(get_social_service)):
    try:
        db_user = service.authenticate_user(user.email, user.password)
    except ValueError as e:
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


@router.put("/update-profile-picture")
def update_profile_picture(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    try:
        new_profile_picture = service.update_user_profile_picture(current_user.id, file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Profile picture updated successfully", "profile_picture": new_profile_picture}


@router.get("/me")
def get_current_logged_in_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/lookup/userid/{username}")
def get_user_id_by_username(
    username: str,
    service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user)  # 🔒 protect route
):
    user = service.user_repo.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id}

@router.get("/lookup/username/{user_id}")
def get_username_by_id(
    user_id: int,
    service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user)  # 🔒 secured
):
    try:
        username = service.get_username_by_id(user_id)
        return {"username": username}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/search", response_model=List[UserResponse])
def search_users(username: str, service: SocialService = Depends(get_social_service)):
    users = service.search_users(username)

    # Fix profile_picture URLs
    result = []
    for user in users:
        if user.profile_picture and not user.profile_picture.startswith("http"):
            user.profile_picture = f"{BASE_URL}{user.profile_picture}"
        result.append(user)

    return result



