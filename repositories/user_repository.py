from sqlalchemy.orm import Session
from models.user import User
from app_utils.security import hash_password


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()

    def search_users(self, username: str):
        return self.db.query(User).filter(User.username.ilike(f"%{username}%")).all()

    def create_user(self, username: str, email: str, password: str):
        hashed_password = hash_password(password)  # Hash the password
        print(f"[DEBUG] Hashed password for {email}: {hashed_password}")

        new_user = User(username=username, email=email, password_hash=hash_password(password))
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def update_profile_picture(self, user_id: int, url: str):
        user = self.get_user_by_id(user_id)
        if user:
            user.profile_picture = url
            self.db.commit()
            self.db.refresh(user)
        return user


