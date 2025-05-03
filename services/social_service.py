import json
import os
import shutil
import uuid

from sqlalchemy.orm import Session

from RL.utils_model.calories_config import CALORIE_RANGES
from app_utils.websocket_manager import send_notification, active_connections

from models.post import Post
from repositories.meal_recommendation_repository import MealRecommendationRepository
from repositories.meal_repository import MealRepository
from repositories.user_repository import UserRepository
from repositories.post_repository import PostRepository
from repositories.friendship_repository import FriendshipRepository
from app_utils.security import verify_password
from RL.utils_model.recommend_meals import recommend_meals
from schemas.comment import CommentResponse
from schemas.like import LikeResponse
from schemas.meal import MealResponse
from schemas.meal_recommendation import MealRecommendationResponse
from schemas.post import PostResponse, MealStatisticsResponse
from datetime import datetime, date
from typing import Optional, Dict, List

UPLOAD_DIR = "static/profile_pictures/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

POST_IMAGE_DIR = "static/post_pictures/"
os.makedirs(POST_IMAGE_DIR, exist_ok=True)

MAX_FILE_SIZE = 2 * 1024 * 1024

BASE_URL = "http://localhost:8000"


class SocialService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
        self.post_repo = PostRepository(db)
        self.friendship_repo = FriendshipRepository(db)
        self.meal_repo = MealRepository(db)
        self.meal_recommendation_repo = MealRecommendationRepository(db)
        self.db = db

        ####### USER SERVICES

    def register_user(self, username: str, email: str, password: str, file):
        existing_user = self.user_repo.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists.")

        existing_username = self.user_repo.get_user_by_username(username)
        if existing_username:
            raise ValueError("Username already taken.")

        new_user = self.user_repo.create_user(username, email, password)
        new_user.profile_picture = self._save_profile_picture(new_user.id, file)

        self.db.commit()
        return new_user

    def authenticate_user(self, email: str, password: str):
        user = self.user_repo.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials.")
        return user

    def update_user_profile_picture(self, user_id: int, file):
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        user.profile_picture = self._save_profile_picture(user_id, file)

        self.db.commit()
        self.db.refresh(user)

        return user.profile_picture

    # social_service.py

    def get_username_by_id(self, user_id: int) -> str:
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        return user.username

    def search_users(self, username: str):
        return self.user_repo.search_users(username)

    ##### FRIENDSHIP SERVICES

    async def send_friend_request(self, sender_id: int, receiver_id: int):
        if sender_id == receiver_id:
            raise ValueError("You cannot send a friend request to yourself.")

        existing_request = self.friendship_repo.get_friendship(sender_id, receiver_id)

        if existing_request:
            if existing_request.status == "accepted":
                raise ValueError("You are already friends.")
            elif existing_request.status == "pending":
                raise ValueError("Friend request already sent.")
            elif existing_request.status == "rejected":
                self.friendship_repo.delete_friendship(existing_request.id)

        await send_notification(
            user_id=receiver_id,
            event_type="friend_request",
            message="You have a new friend request!",
            data={"sender_id": sender_id}
        )

        return self.friendship_repo.create_friend_request(sender_id, receiver_id)

    async def accept_friend_request(self, request_id: int, user_id: int):
        friendship = self.friendship_repo.get_friendship_by_id(request_id)
        if not friendship or friendship.receiver_id != user_id:
            raise ValueError("Friend request not found or not meant for you.")
        if friendship.status != "pending":
            raise ValueError("Friend request already accepted or rejected.")

        friendship.status = "accepted"
        self.db.commit()

        await send_notification(
            user_id=friendship.sender_id,
            event_type="friend_accepted",
            message="Your friend request was accepted!",
            data={"friend_id": friendship.receiver_id}
        )
        await send_notification(
            user_id=user_id,
            event_type="friend_accepted",
            message="You are now friends!",
            data={"friend_id": friendship.sender_id}
        )

        return friendship

    def reject_friend_request(self, request_id: int, user_id: int):
        friendship = self.friendship_repo.get_friendship_by_id(request_id)
        if not friendship or friendship.receiver_id != user_id:
            raise ValueError("Friend request not found or not meant for you.")

        self.db.delete(friendship)
        self.db.commit()
        return "Friend request rejected and removed"

    def remove_friend(self, friendship_id: int):
        return self.friendship_repo.update_friendship_status(friendship_id, "rejected")

    def delete_friend(self, friendship_id: int):
        self.friendship_repo.delete_friendship(friendship_id)

    def view_pending_requests(self, user_id: int):
        return self.friendship_repo.get_pending_requests(user_id)

    def view_friends(self, user_id: int):
        return self.friendship_repo.get_friends(user_id)

    def view_sent_requests(self, user_id: int):
        return self.friendship_repo.get_sent_pending_requests(user_id)

    #  POST SERVICES

    def save_post_image(self, user_id: int, file):
        self._validate_file(file)

        file_extension = file.filename.split(".")[-1].lower()
        unique_id = uuid.uuid4().hex
        file_path = f"{POST_IMAGE_DIR}{user_id}_{unique_id}.{file_extension}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/post_pictures/{user_id}_{unique_id}.{file_extension}"

    async def create_user_post(self, user_id: int, caption: str, file, macros: dict):
        image_url = self.save_post_image(user_id, file) if file else None
        new_post = self.post_repo.create_post(user_id, caption, image_url, macros)

        friends = self.friendship_repo.get_friends(user_id)
        for friend in friends:
            friend_id = friend.sender_id if friend.receiver_id == user_id else friend.receiver_id
            await send_notification(
                user_id=friend_id,
                event_type="post_created",
                message=f"{new_post.user.username} posted a new update!",
                data={"post_id": new_post.id}
            )

        return PostResponse(
            id=new_post.id,
            user_id=new_post.user_id,
            username=new_post.user.username,
            caption=new_post.caption,
            image_url=f"{BASE_URL}{new_post.image_url}" if new_post.image_url else None,
            macros=new_post.macros,
            created_at=new_post.created_at,
            likes_count=len(new_post.likes),
            comments_count=len(new_post.comments),
        )

    def update_user_post(self, post_id: int, user_id: int, caption: str = None, file=None, macros: dict = None):
        post = self.post_repo.get_post_by_id(post_id)
        if not post or post.user_id != user_id:
            raise ValueError("Post not found or unauthorized.")

        if post.image_url and file:
            old_image_path = post.image_url.replace(BASE_URL, "").lstrip("/")
            full_old_path = os.path.join("static", old_image_path)
            if os.path.exists(full_old_path):
                os.remove(full_old_path)

        image_url = self.save_post_image(user_id, file) if file else post.image_url

        updated_post = self.post_repo.update_post(post_id, user_id, caption, image_url, macros)
        if not updated_post:
            raise ValueError("Post update failed.")

        return updated_post

    def delete_user_post(self, post_id: int, user_id: int):
        post = self.post_repo.get_post_by_id(post_id)
        if not post or post.user_id != user_id:
            raise ValueError("Post not found or unauthorized.")

        if post.image_url:
            image_path = post.image_url.replace(BASE_URL, "").lstrip("/")
            full_path = os.path.join("static", image_path)

            if os.path.exists(full_path):
                os.remove(full_path)

        if not self.post_repo.delete_post(post_id, user_id):
            raise ValueError("Post not found or unauthorized.")

        return {"message": "Post deleted successfully"}

    def get_user_feed(self, user_id: int) -> list[PostResponse]:

        friends = self.friendship_repo.get_friends(user_id)
        friend_ids = [friend.sender_id if friend.receiver_id == user_id else friend.receiver_id for friend in friends]

        if not friend_ids:
            return []

        posts = self.post_repo.get_posts_by_user_ids(friend_ids)

        return [
            PostResponse(
                id=post.id,
                user_id=post.user_id,
                username=self.user_repo.get_user_by_id(post.user_id).username,
                caption=post.caption,
                image_url=post.image_url if post.image_url and post.image_url.startswith("http") else f"{BASE_URL}{post.image_url}" if post.image_url else None
,
                macros=post.macros,
                created_at=post.created_at,
                likes=[LikeResponse(id=like.id, user_id=like.user_id, post_id=like.post_id) for like in post.likes],
                comments=[CommentResponse(id=comment.id, user_id=comment.user_id,
                                          username=self.user_repo.get_user_by_id(comment.user_id).username,
                                          post_id=comment.post_id,
                                          text=comment.text, created_at=comment.created_at) for comment in
                          post.comments],
            ) for post in sorted(posts, key=lambda post: post.created_at, reverse=True)
        ]

    def get_user_posts(self, user_id: int):
        """
        Retrieves all posts created by a specific user.
        """
        posts = self.post_repo.get_posts_by_user(user_id)
        if not posts:
            raise ValueError("No posts found for this user.")

        return [
            PostResponse(
                id=post.id,
                user_id=post.user_id,
                username=self.user_repo.get_user_by_id(post.user_id).username,
                caption=post.caption,
                image_url=post.image_url if post.image_url and post.image_url.startswith("http") else f"{BASE_URL}{post.image_url}" if post.image_url else None
,
                macros=post.macros,
                created_at=post.created_at,
                likes=[LikeResponse(id=like.id, user_id=like.user_id, post_id=like.post_id) for like in post.likes],
                comments=[CommentResponse(id=comment.id, user_id=comment.user_id,
                                          username=self.user_repo.get_user_by_id(comment.user_id).username,
                                          post_id=comment.post_id,
                                          text=comment.text, created_at=comment.created_at) for comment in
                          post.comments],
            ) for post in sorted(posts, key=lambda post: post.created_at, reverse=True)
        ]

    def get_post_by_id(self, post_id: int):
        post = self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ValueError("Post not found")

        image_url = post.image_url if post.image_url and post.image_url.startswith("http") else f"{BASE_URL}{post.image_url}" if post.image_url else None
        print(post.id, post.image_url, post.macros)
        print("DEBUG: image_url is", image_url)

        return PostResponse(
            id=post.id,
            user_id=post.user_id,
            username=self.user_repo.get_user_by_id(post.user_id).username,
            caption=post.caption,
            image_url=f"{BASE_URL}{post.image_url}" if post.image_url else None,
            macros=post.macros,
            created_at=post.created_at,
            likes=[
                LikeResponse(id=like.id, user_id=like.user_id, post_id=like.post_id)
                for like in post.likes
            ],
            comments=[
                CommentResponse(
                    id=comment.id,
                    user_id=comment.user_id,
                    username=self.user_repo.get_user_by_id(comment.user_id).username,
                    post_id=comment.post_id,
                    text=comment.text,
                    created_at=comment.created_at
                )
                for comment in post.comments
            ],
        )

    def _validate_file(self, file):
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ["jpg", "jpeg", "png"]:
            raise ValueError("Invalid file format. Only JPG and PNG are allowed.")

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > MAX_FILE_SIZE:
            raise ValueError("File size must be less than 2MB.")

    def _save_profile_picture(self, user_id: int, file):
        self._validate_file(file)

        file_extension = file.filename.split(".")[-1].lower()
        file_path = f"{UPLOAD_DIR}{user_id}.{file_extension}"

        old_profile_path = f"static{file_path}"
        if os.path.exists(old_profile_path):
            os.remove(old_profile_path)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"{BASE_URL}/profile_pictures/{user_id}.{file_extension}"

    async def like_post(self, user_id: int, post_id: int):

        post = self._validate_post_access(user_id, post_id)  # ✅ Reuse validation

        like = self.post_repo.add_like(user_id, post_id)
        if not like:
            raise ValueError("You already liked this post.")

        await send_notification(
            user_id=post.user_id,
            event_type="post_liked",
            message=f"{self.user_repo.get_user_by_id(user_id).username} liked your post!",
            data={"post_id": post_id}
        )

        return LikeResponse(
            id=like.id,
            user_id=like.user_id,
            post_id=like.post_id
        )

    async def unlike_post(self, user_id: int, post_id: int):
        post = self._validate_post_access(user_id, post_id)

        like = self.post_repo.get_like(user_id, post_id)
        if not like:
            raise ValueError("You haven't liked this post.")

        self.post_repo.remove_like(user_id, post_id)
        return {"message": "Like removed successfully"}

    async def comment_on_post(self, user_id: int, post_id: int, text: str) -> CommentResponse:
        if len(text.strip()) == 0:
            raise ValueError("Comment cannot be empty.")

        post = self._validate_post_access(user_id, post_id)

        user_comments = [comment for comment in post.comments if comment.user_id == user_id]

        if len(user_comments) >= 3:
            raise ValueError("You can only comment up to 3 times on the same post.")

        comment = self.post_repo.add_comment(user_id, post_id, text)

        if post_id in active_connections:
            await active_connections[post_id].send_json({
                "post_id": post_id,
                "comments": [
                    {
                        "id": c.id,
                        "user_id": c.user_id,
                        "username": self.user_repo.get_user_by_id(c.user_id).username,
                        "post_id": c.post_id,
                        "text": c.text,
                        "created_at": c.created_at.isoformat()
                    }
                    for c in post.comments
                ]
            })

        if post.user_id != user_id:
            await send_notification(
                user_id=post.user_id,
                event_type="new_comment",
                message=f"{self.user_repo.get_user_by_id(user_id).username} commented on your post!",
                data={"post_id": post_id, "comment": text}
            )

        return CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            username=self.user_repo.get_user_by_id(comment.user_id).username,
            post_id=comment.post_id,
            text=comment.text,
            created_at=comment.created_at
        )

    def get_comments(self, user_id: int, post_id: int):
        post = self._validate_post_access(user_id, post_id)

        comments = self.post_repo.get_comments_for_post(post_id)
        return comments

    def _validate_post_access(self, user_id: int, post_id: int):

        post = self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ValueError("Post not found.")

        friends = self.friendship_repo.get_friends(user_id)
        friend_ids = {friend.sender_id if friend.receiver_id == user_id else friend.receiver_id for friend in friends}

        if post.user_id != user_id and post.user_id not in friend_ids:
            raise ValueError("You can only interact with your own posts or your friends' posts.")

        return post

    ####### MEAL SERVICES

    def get_meal_recommendations(self, user_id: int, profile: str, target_calories: int) -> MealRecommendationResponse:
        """
        Fetch recommended meals from the RL system, save them automatically, and return structured responses.
        """
        if profile not in CALORIE_RANGES:
            raise ValueError(f"Invalid profile '{profile}'. Allowed: {list(CALORIE_RANGES.keys())}")

        if target_calories not in CALORIE_RANGES[profile]:
            raise ValueError(f"Invalid calorie target '{target_calories}' for {profile}. "
                             f"Allowed: {list(CALORIE_RANGES[profile])}")

        # 🔹 Call the RL function to get recommended meals
        recommended_meals = recommend_meals(profile, target_calories)

        if not recommended_meals:
            raise ValueError(f"No recommendations available for {profile} at {target_calories} kcal.")

        meal_ids = [meal.id for meal in recommended_meals]

        saved_recommendation = self.meal_recommendation_repo.create_recommendation(user_id, profile, target_calories,
                                                                                   meal_ids)

        return MealRecommendationResponse(
            id=saved_recommendation.id,
            user_id=saved_recommendation.user_id,
            profile_type=saved_recommendation.profile_type,
            target_calories=saved_recommendation.target_calories,
            meals=[
                MealResponse(
                    id=meal.id,
                    name=meal.name,
                    calories=meal.calories,
                    protein=meal.protein,
                    carbs=meal.carbs,
                    fats=meal.fats,
                    photo_url=meal.photo_url,
                    ingredients=json.loads(meal.ingredients) if isinstance(meal.ingredients, str) else meal.ingredients
                ) for meal in saved_recommendation.meals
            ]
        )

    def save_meal_recommendation(self, user_id: int, profile_type: str, target_calories: int, meal_ids: list[int]):

        return self.meal_recommendation_repo.create_recommendation(user_id, profile_type, target_calories, meal_ids)

    def get_user_meal_recommendations(self, user_id: int):

        recommendations = self.meal_recommendation_repo.get_user_recommendations(user_id)
        return [
            MealRecommendationResponse(
                id=rec.id,
                user_id=rec.user_id,
                profile_type=rec.profile_type,
                target_calories=rec.target_calories,
                meals=[
                    MealResponse(
                        id=meal.id,
                        name=meal.name,
                        calories=meal.calories,
                        protein=meal.protein,
                        carbs=meal.carbs,
                        fats=meal.fats,
                        photo_url=meal.photo_url,
                        ingredients=json.loads(meal.ingredients)
                    ) for meal in rec.meals
                ]
            )
            for rec in recommendations
        ]

    def delete_meal_recommendation(self, user_id: int, recommendation_id: int):

        deleted = self.meal_recommendation_repo.delete_recommendation(user_id, recommendation_id)

        if not deleted:
            raise ValueError(f"Meal recommendation with ID {recommendation_id} not found for user {user_id}.")

        return {"message": "Meal recommendation deleted successfully"}

    #### Statistics

    def _aggregate_daily_macros(self, posts: List[Post]) -> Dict[date, dict]:

        daily_macros = {}
        for post in posts:
            post_date = post.created_at.date()
            if post_date not in daily_macros:
                daily_macros[post_date] = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}

            macros = post.macros
            if macros:
                daily_macros[post_date]['calories'] += macros.get('calories', 0)
                daily_macros[post_date]['protein'] += macros.get('protein', 0)
                daily_macros[post_date]['carbs'] += macros.get('carbs', 0)
                daily_macros[post_date]['fats'] += macros.get('fats', 0)

        return daily_macros

    def _filter_days_above_threshold(self, daily_macros: Dict[date, dict], calorie_threshold: int = 800) -> List[
        dict]:

        return [day for day in daily_macros.values() if day['calories'] >= calorie_threshold]

    def _calculate_averages(self, filtered_days: List[dict]) -> dict:
        if not filtered_days:
            return {
                "average_calories": 0,
                "average_protein": 0,
                "average_carbs": 0,
                "average_fats": 0,
                "total_days_considered": 0
            }

        total_days = len(filtered_days)

        total_macros = {
            "average_calories": sum(day['calories'] for day in filtered_days) / total_days,
            "average_protein": sum(day['protein'] for day in filtered_days) / total_days,
            "average_carbs": sum(day['carbs'] for day in filtered_days) / total_days,
            "average_fats": sum(day['fats'] for day in filtered_days) / total_days,
            "total_days_considered": total_days
        }

        return total_macros

    def _calculate_distribution(self, filtered_days: List[dict]) -> dict:
        if not filtered_days:
            return {
                "protein_distribution": 0.0,
                "carbs_distribution": 0.0,
                "fats_distribution": 0.0
            }

        total_protein = sum(day['protein'] for day in filtered_days)
        total_carbs = sum(day['carbs'] for day in filtered_days)
        total_fats = sum(day['fats'] for day in filtered_days)
        total_calories = (
                total_protein * 4 +  # 1g protein = 4 kcal
                total_carbs * 4 +  # 1g carbs = 4 kcal
                total_fats * 9  # 1g fat = 9 kcal
        )

        if total_calories == 0:
            return {
                "protein_distribution": 0.0,
                "carbs_distribution": 0.0,
                "fats_distribution": 0.0
            }

        return {
            "protein_distribution": round((total_protein * 4 / total_calories) * 100, 2),
            "carbs_distribution": round((total_carbs * 4 / total_calories) * 100, 2),
            "fats_distribution": round((total_fats * 9 / total_calories) * 100, 2)
        }

    def get_user_nutrition_statistics(self, user_id: int, start_date: str, end_date: str) -> MealStatisticsResponse:

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

            posts = self.post_repo.get_user_posts_in_range(user_id, start_date, end_date)
            daily_macros = self._aggregate_daily_macros(posts)
            filtered_days = self._filter_days_above_threshold(daily_macros)

            average_macros = self._calculate_averages(filtered_days)
            distribution = self._calculate_distribution(filtered_days)

            result = {**average_macros, **distribution}

            return MealStatisticsResponse(**result)

        except ValueError as e:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    def get_user_by_id(self, user_id):
        return self.user_repo.get_user_by_id(user_id)
