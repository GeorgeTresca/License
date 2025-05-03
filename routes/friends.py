from fastapi import APIRouter, Depends, HTTPException
from schemas.friendship import FriendRequest, FriendResponse
from app_utils.security import get_current_user
from services.social_service import SocialService
from app_utils.dependencies import get_social_service

router = APIRouter()

connected_users = {}


async def notify_user(user_id: int, message: str):
    if user_id in connected_users:
        await connected_users[user_id].send_text(message)


@router.post("/send-request")
async def send_request(
        request: FriendRequest,
        current_user=Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    try:
        result = await service.send_friend_request(current_user.id, request.receiver_id)
        if isinstance(result, str):
            raise HTTPException(status_code=400, detail=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await notify_user(request.receiver_id, f"New friend request from {current_user.username}")
    return result


@router.post("/accept-request/{request_id}")
async def accept_request(
        request_id: int,
        current_user=Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    try:
        result = await service.accept_friend_request(request_id, current_user.id)
        if isinstance(result, str):
            raise HTTPException(status_code=400, detail=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await notify_user(result.sender_id, f"{current_user.username} accepted your friend request")
    await notify_user(current_user.id,
                      f"You are now friends with a new person.")

    return {"message": "Friend request accepted"}


@router.post("/reject-request/{request_id}")
def reject_request(
        request_id: int,
        current_user=Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    try:
        result = service.reject_friend_request(request_id, current_user.id)
        if isinstance(result, str):
            raise HTTPException(status_code=400, detail=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Friend request rejected"}


@router.delete("/remove-friend/{friend_id}")
def remove_friendship(
        friend_id: int,
        service: SocialService = Depends(get_social_service)
):
    service.delete_friend(friend_id)
    return {"message": "Friend removed successfully"}


@router.get("/pending-requests", response_model=list[FriendResponse])
def pending_requests(
        current_user=Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    return service.view_pending_requests(current_user.id)


@router.get("/sent-requests", response_model=list[FriendResponse])
def sent_requests(
        current_user=Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    return service.view_sent_requests(current_user.id)

@router.get("/friends", response_model=list[FriendResponse])
def get_friends(
        current_user=Depends(get_current_user),
        service: SocialService = Depends(get_social_service)
):
    return service.view_friends(current_user.id)
