# services/friend_service.py
from sqlalchemy.orm import Session
from repositories.friendship_repository import FriendshipRepository

class FriendService:
    def __init__(self, friendship_repo: FriendshipRepository):
        self.friendship_repo = friendship_repo

    def send_friend_request(self, sender_id: int, receiver_id: int):
        if sender_id == receiver_id:
            raise ValueError("You cannot send a friend request to yourself.")

        existing = self.friendship_repo.get_friendship(sender_id, receiver_id)
        if existing:
            if existing.status == "accepted":
                raise ValueError("You are already friends.")
            if existing.status == "pending":
                raise ValueError("Friend request already sent.")
            if existing.status == "rejected":
                self.friendship_repo.delete_friendship(existing.id)

        return self.friendship_repo.create_friend_request(sender_id, receiver_id)

    def accept_friend_request(self, request_id: int, user_id: int):
        friendship = self.friendship_repo.get_friendship_by_id(request_id)
        if not friendship or friendship.receiver_id != user_id:
            raise ValueError("Friend request not found or not meant for you.")
        if friendship.status != "pending":
            raise ValueError("Friend request already accepted or rejected.")

        friendship.status = "accepted"
        self.friendship_repo.db.commit()
        return friendship

    def reject_friend_request(self, request_id: int, user_id: int):
        friendship = self.friendship_repo.get_friendship_by_id(request_id)
        if not friendship or friendship.receiver_id != user_id:
            raise ValueError("Friend request not found or not meant for you.")

        self.friendship_repo.db.delete(friendship)
        self.friendship_repo.db.commit()
        return "Friend request rejected and removed"

    def delete_friend(self, friendship_id: int):
        self.friendship_repo.delete_friendship(friendship_id)

    def remove_friend(self, friendship_id: int):
        return self.friendship_repo.update_friendship_status(friendship_id, "rejected")

    def view_pending_requests(self, user_id: int):
        return self.friendship_repo.get_pending_requests(user_id)

    def view_sent_requests(self, user_id: int):
        return self.friendship_repo.get_sent_pending_requests(user_id)

    def view_friends(self, user_id: int):
        return self.friendship_repo.get_friends(user_id)
