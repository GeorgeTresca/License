# services/user_service.py
import os
import shutil
import uuid
from sqlalchemy.orm import Session
from app_utils.security import verify_password
from models.user import User
from schemas.user import UserResponse

BASE_URL = "http://localhost:8000"
UPLOAD_DIR = "static/profile_pictures/"
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 2 * 1024 * 1024

class UserService:
    def __init__(self, user_repo):
        self.user_repo = user_repo

    def register_user(self, username: str, email: str, password: str, file):
        if self.user_repo.get_user_by_email(email):
            raise ValueError("User with this email already exists.")
        if self.user_repo.get_user_by_username(username):
            raise ValueError("Username already taken.")

        new_user = self.user_repo.create_user(username, email, password)
        profile_url = self._save_profile_picture(new_user.id, file)
        new_user = self.user_repo.update_profile_picture(new_user.id, profile_url)
        return new_user

    def authenticate_user(self, email: str, password: str):
        user = self.user_repo.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials.")
        return user

    def get_username_by_id(self, user_id: int) -> str:
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        return user.username

    def search_users(self, username: str):
        return self.user_repo.search_users(username)

    def get_user_by_username(self, username: str) -> User:
        return self.user_repo.get_user_by_username(username)

    def _validate_file(self, file):
        if file.filename.split(".")[-1].lower() not in ["jpg", "jpeg", "png"]:
            raise ValueError("Invalid file format. Only JPG and PNG are allowed.")

        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        if size > MAX_FILE_SIZE:
            raise ValueError("File size must be less than 2MB.")

    def _save_profile_picture(self, user_id: int, file):
        self._validate_file(file)
        ext = file.filename.split(".")[-1].lower()
        path = f"{UPLOAD_DIR}{user_id}.{ext}"

        if os.path.exists(path):
            os.remove(path)

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/profile_pictures/{user_id}.{ext}"


