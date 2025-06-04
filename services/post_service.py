# services/post_service.py
import os
import uuid
import shutil
from typing import List, Dict
from datetime import datetime, date
from models.post import Post
from schemas.post import PostResponse, MealStatisticsResponse
from schemas.comment import CommentResponse
from schemas.like import LikeResponse

BASE_URL = "http://localhost:8000"
POST_IMAGE_DIR = "static/post_pictures/"
MAX_FILE_SIZE = 2 * 1024 * 1024
os.makedirs(POST_IMAGE_DIR, exist_ok=True)

class PostService:
    def __init__(self, user_repo, post_repo, friendship_repo):
        self.user_repo = user_repo
        self.post_repo = post_repo
        self.friendship_repo = friendship_repo

    def save_post_image(self, user_id: int, file):
        self._validate_file(file)
        ext = file.filename.split(".")[-1].lower()
        path = f"{POST_IMAGE_DIR}{user_id}_{uuid.uuid4().hex}.{ext}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/post_pictures/{os.path.basename(path)}"

    def create_user_post(self, user_id: int, caption: str, file, macros: dict):
        image_url = self.save_post_image(user_id, file) if file else None
        new_post = self.post_repo.create_post(user_id, caption, image_url, macros)

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

    def get_user_feed(self, user_id: int) -> List[PostResponse]:
        friends = self.friendship_repo.get_friends(user_id)
        friend_ids = [f.sender_id if f.receiver_id == user_id else f.receiver_id for f in friends]
        if not friend_ids:
            return []

        posts = self.post_repo.get_posts_by_user_ids(friend_ids)
        return self._serialize_posts(posts)

    def get_user_posts(self, user_id: int):
        posts = self.post_repo.get_posts_by_user(user_id)
        # if not posts:
        #     raise ValueError("No posts found for this user.")
        return self._serialize_posts(posts)

    def get_post_by_id(self, post_id: int):
        post = self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ValueError("Post not found.")
        return self._serialize_post(post)

    def like_post(self, user_id: int, post_id: int):
        post = self._validate_post_access(user_id, post_id)
        like = self.post_repo.add_like(user_id, post_id)
        if not like:
            raise ValueError("You already liked this post.")
        return LikeResponse(id=like.id, user_id=like.user_id, post_id=like.post_id)

    def unlike_post(self, user_id: int, post_id: int):
        post = self._validate_post_access(user_id, post_id)
        like = self.post_repo.get_like(user_id, post_id)
        if not like:
            raise ValueError("You haven't liked this post.")
        self.post_repo.remove_like(user_id, post_id)
        return {"message": "Like removed successfully"}

    def comment_on_post(self, user_id: int, post_id: int, text: str) -> CommentResponse:
        if len(text.strip()) == 0:
            raise ValueError("Comment cannot be empty.")
        post = self._validate_post_access(user_id, post_id)
        if len([c for c in post.comments if c.user_id == user_id]) >= 3:
            raise ValueError("You can only comment up to 3 times on the same post.")
        comment = self.post_repo.add_comment(user_id, post_id, text)
        return CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            username=self.user_repo.get_user_by_id(comment.user_id).username,
            post_id=comment.post_id,
            text=comment.text,
            created_at=comment.created_at
        )

    def get_user_nutrition_statistics(self, user_id: int, start_date: str, end_date: str) -> MealStatisticsResponse:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            posts = self.post_repo.get_user_posts_in_range(user_id, start, end)
            daily_macros = self._aggregate_daily_macros(posts)
            filtered = self._filter_days_above_threshold(daily_macros)
            averages = self._calculate_averages(filtered)
            dist = self._calculate_distribution(filtered)
            return MealStatisticsResponse(**{**averages, **dist})
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    # ------------------ Helpers ------------------

    def _validate_file(self, file):
        if file.filename.split(".")[-1].lower() not in ["jpg", "jpeg", "png"]:
            raise ValueError("Invalid file format.")
        file.file.seek(0, os.SEEK_END)
        if file.file.tell() > MAX_FILE_SIZE:
            raise ValueError("File size must be less than 2MB.")
        file.file.seek(0)

    def _validate_post_access(self, user_id: int, post_id: int):
        post = self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ValueError("Post not found.")
        friends = self.friendship_repo.get_friends(user_id)
        friend_ids = {f.sender_id if f.receiver_id == user_id else f.receiver_id for f in friends}
        if post.user_id != user_id and post.user_id not in friend_ids:
            raise ValueError("Access denied.")
        return post

    def _serialize_posts(self, posts: List[Post]):
        return [self._serialize_post(post) for post in sorted(posts, key=lambda p: p.created_at, reverse=True)]

    def _serialize_post(self, post: Post) -> PostResponse:
        return PostResponse(
            id=post.id,
            user_id=post.user_id,
            username=self.user_repo.get_user_by_id(post.user_id).username,
            caption=post.caption,
            image_url=f"{BASE_URL}{post.image_url}" if post.image_url and not post.image_url.startswith("http") else post.image_url,
            macros=post.macros,
            created_at=post.created_at,
            likes=[LikeResponse(id=l.id, user_id=l.user_id, post_id=l.post_id) for l in post.likes],
            comments=[
                CommentResponse(
                    id=c.id,
                    user_id=c.user_id,
                    username=self.user_repo.get_user_by_id(c.user_id).username,
                    post_id=c.post_id,
                    text=c.text,
                    created_at=c.created_at
                ) for c in post.comments
            ],
        )

    def _aggregate_daily_macros(self, posts: List[Post]) -> Dict[date, dict]:
        result = {}
        for post in posts:
            d = post.created_at.date()
            result.setdefault(d, {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0})
            for macro in ['calories', 'protein', 'carbs', 'fats']:
                result[d][macro] += post.macros.get(macro, 0)
        return result

    def _filter_days_above_threshold(self, macros: Dict[date, dict], threshold: int = 800):
        return [day for day in macros.values() if day['calories'] >= threshold]

    def _calculate_averages(self, days: List[dict]) -> dict:
        if not days:
            return {"average_calories": 0, "average_protein": 0, "average_carbs": 0, "average_fats": 0, "total_days_considered": 0}
        total = len(days)
        return {
            "average_calories": sum(d['calories'] for d in days) / total,
            "average_protein": sum(d['protein'] for d in days) / total,
            "average_carbs": sum(d['carbs'] for d in days) / total,
            "average_fats": sum(d['fats'] for d in days) / total,
            "total_days_considered": total
        }

    def _calculate_distribution(self, days: List[dict]) -> dict:
        if not days:
            return {"protein_distribution": 0, "carbs_distribution": 0, "fats_distribution": 0}
        protein = sum(d['protein'] for d in days)
        carbs = sum(d['carbs'] for d in days)
        fats = sum(d['fats'] for d in days)
        total_kcal = protein * 4 + carbs * 4 + fats * 9
        if total_kcal == 0:
            return {"protein_distribution": 0, "carbs_distribution": 0, "fats_distribution": 0}
        return {
            "protein_distribution": round((protein * 4 / total_kcal) * 100, 2),
            "carbs_distribution": round((carbs * 4 / total_kcal) * 100, 2),
            "fats_distribution": round((fats * 9 / total_kcal) * 100, 2)
        }
