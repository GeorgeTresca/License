import json

active_connections = {}


async def send_notification(user_id: int, event_type: str, message: str, data: dict = None):
    """Send a structured WebSocket notification to a user."""
    websocket = active_connections.get(user_id)
    if websocket:
        notification = {
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        await websocket.send_text(json.dumps(notification))
