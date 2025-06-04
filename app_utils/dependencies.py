from fastapi import Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from repositories.friendship_repository import FriendshipRepository
from repositories.meal_recommendation_repository import MealRecommendationRepository
from repositories.meal_repository import MealRepository
from repositories.post_repository import PostRepository
from repositories.user_repository import UserRepository
from services.friend_service import FriendService
from services.meal_service import MealService
from services.post_service import PostService
from services.user_service import UserService


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_service(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    return UserService(user_repo)


def get_friend_service(db: Session = Depends(get_db)):
    return FriendService(FriendshipRepository(db))


def get_post_service(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    post_repo = PostRepository(db)
    friendship_repo = FriendshipRepository(db)
    return PostService(user_repo, post_repo, friendship_repo)

def get_meal_service(db: Session = Depends(get_db)):
    meal_repo = MealRepository(db)
    meal_rec_repo = MealRecommendationRepository(db)
    return MealService(meal_repo, meal_rec_repo)