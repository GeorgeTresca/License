from sqlalchemy.orm import Session
from models.friendship import Friendship


class FriendshipRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_friendship(self, sender_id: int, receiver_id: int):

        return self.db.query(Friendship).filter(
            Friendship.sender_id == sender_id, Friendship.receiver_id == receiver_id
        ).first()

    def get_friendship_by_id(self, friendship_id: int):

        return self.db.query(Friendship).filter(Friendship.id == friendship_id).first()

    def create_friend_request(self, sender_id: int, receiver_id: int):

        friend_request = Friendship(sender_id=sender_id, receiver_id=receiver_id, status="pending")
        self.db.add(friend_request)
        self.db.commit()
        self.db.refresh(friend_request)
        return friend_request

    def update_friendship_status(self, friendship_id: int, status: str):

        friendship = self.db.query(Friendship).filter(Friendship.id == friendship_id).first()
        if friendship:
            friendship.status = status
            self.db.commit()
        return friendship

    def delete_friendship(self, friendship_id: int):

        friendship = self.db.query(Friendship).filter(Friendship.id == friendship_id).first()
        if friendship:
            self.db.delete(friendship)
            self.db.commit()

    def get_pending_requests(self, user_id: int):

        return self.db.query(Friendship).filter(
            Friendship.receiver_id == user_id, Friendship.status == "pending"
        ).all()

    def get_friends(self, user_id: int):

        return self.db.query(Friendship).filter(
            ((Friendship.sender_id == user_id) | (Friendship.receiver_id == user_id)),
            Friendship.status == "accepted"
        ).all()

    def get_sent_pending_requests(self, user_id: int):

        return self.db.query(Friendship).filter(
            Friendship.sender_id == user_id, Friendship.status == "pending"
        ).all()
