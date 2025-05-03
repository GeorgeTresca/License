from sqlalchemy.orm import Session
from models.comment import Comment
from models.like import Like
from models.post import Post
from models.friendship import Friendship
from datetime import datetime, timedelta
from typing import List


class PostRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_post_by_id(self, post_id: int):

        return self.db.query(Post).filter(Post.id == post_id).first()

    def create_post(self, user_id: int, caption: str, image_url: str, macros: dict):

        new_post = Post(user_id=user_id, caption=caption, image_url=image_url, macros=macros)
        self.db.add(new_post)
        self.db.commit()
        self.db.refresh(new_post)
        return new_post


    def update_post(self, post_id: int, user_id: int, caption: str = None, image_url: str = None, macros: dict = None):

        post = self.db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
        if not post:
            return None
        if caption is not None:
            post.caption = caption
        if image_url is not None:
            post.image_url = image_url
        if macros is not None:
            post.macros = macros
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete_post(self, post_id: int, user_id: int):

        post = self.db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
        if not post:
            return None
        self.db.delete(post)
        self.db.commit()
        return True

    def get_posts_by_user_ids(self, user_ids):

        return self.db.query(Post).filter(Post.user_id.in_(user_ids)).all()

    def get_post_by_id(self, post_id: int):

        return self.db.query(Post).filter(Post.id == post_id).first()

    def add_like(self, user_id: int, post_id: int):

        existing_like = self.db.query(Like).filter_by(user_id=user_id, post_id=post_id).first()
        if existing_like:
            return None

        like = Like(user_id=user_id, post_id=post_id)
        self.db.add(like)
        self.db.commit()
        return like

    def remove_like(self, user_id: int, post_id: int):

        like = self.db.query(Like).filter_by(user_id=user_id, post_id=post_id).first()
        if like:
            self.db.delete(like)
            self.db.commit()
            return True
        return False

    def add_comment(self, user_id: int, post_id: int, text: str):

        comment = Comment(user_id=user_id, post_id=post_id, text=text)
        self.db.add(comment)
        self.db.commit()
        return comment

    def get_comments_for_post(self, post_id: int):

        return self.db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.desc()).all()

    def get_like(self, user_id, post_id):

            return self.db.query(Like).filter(Like.user_id == user_id, Like.post_id == post_id).first()

    def get_posts_by_user(self, user_id):

            return self.db.query(Post).filter(Post.user_id == user_id).all()

    def get_user_posts_in_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Post]:
        adjusted_end_date = end_date + timedelta(days=1)

        return (
            self.db.query(Post)
            .filter(
                Post.user_id == user_id,
                Post.created_at >= start_date,
                Post.created_at < adjusted_end_date  # Strictly less than next day
            )
            .all()
        )





