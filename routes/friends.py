# friends.py (modificat)
from fastapi import APIRouter, Depends, HTTPException
from schemas.friendship import FriendRequest, FriendResponse
from app_utils.security import get_current_user
from services.friend_service import FriendService
from app_utils.dependencies import get_friend_service

router = APIRouter()

@router.post("/send-request")
def send_request(
        request: FriendRequest,
        current_user=Depends(get_current_user),
        service: FriendService = Depends(get_friend_service)
):
    try:
        result = service.send_friend_request(current_user.id, request.receiver_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result

@router.post("/accept-request/{request_id}")
def accept_request(
        request_id: int,
        current_user=Depends(get_current_user),
        service: FriendService = Depends(get_friend_service)
):
    try:
        service.accept_friend_request(request_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Friend request accepted"}

@router.post("/reject-request/{request_id}")
def reject_request(
        request_id: int,
        current_user=Depends(get_current_user),
        service: FriendService = Depends(get_friend_service)
):
    try:
        service.reject_friend_request(request_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Friend request rejected"}

@router.delete("/remove-friend/{friend_id}")
def remove_friendship(
        friend_id: int,
        service: FriendService = Depends(get_friend_service)
):
    service.delete_friend(friend_id)
    return {"message": "Friend removed successfully"}

@router.get("/pending-requests", response_model=list[FriendResponse])
def pending_requests(
        current_user=Depends(get_current_user),
        service: FriendService = Depends(get_friend_service)
):
    return service.view_pending_requests(current_user.id)

@router.get("/sent-requests", response_model=list[FriendResponse])
def sent_requests(
        current_user=Depends(get_current_user),
        service: FriendService = Depends(get_friend_service)
):
    return service.view_sent_requests(current_user.id)

@router.get("/friends", response_model=list[FriendResponse])
def get_friends(
        current_user=Depends(get_current_user),
        service: FriendService = Depends(get_friend_service)
):
    return service.view_friends(current_user.id)
