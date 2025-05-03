import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware

from app_utils.websocket_manager import active_connections
from database import Base, engine, SessionLocal
from fastapi import FastAPI, Depends
from routes import auth, friends, posts, meals
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Meal Planner API", version="1.0")

Base.metadata.create_all(bind=engine)


app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(friends.router, prefix="/friends", tags=["Friends"])
app.include_router(posts.router, prefix="/posts", tags=["Posts"])
app.include_router(meals.router, prefix="/meals", tags=["Meals"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8100", "http://localhost:8000", "http://192.168.0.*:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    active_connections[user_id] = websocket  # Store WebSocket in active connections

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Received message: {data}")
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {user_id}")
        active_connections.pop(user_id, None)


UPLOAD_DIR = "static/profile_pictures/"
POST_IMAGE_DIR = "static/post_pictures/"
RECIPE_IMAGE_DIR = "static/recipe_images/"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(POST_IMAGE_DIR, exist_ok=True)

app.mount("/profile_pictures", StaticFiles(directory=UPLOAD_DIR), name="profile_pictures")
app.mount("/post_pictures", StaticFiles(directory=POST_IMAGE_DIR), name="post_pictures")
app.mount("/recipe_images", StaticFiles(directory=RECIPE_IMAGE_DIR), name="recipe_images")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Meal Planner API",
        version="1.0",
        description="API for meal planning and social features",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" in method:
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi


@app.get("/")
def home():
    return {"message": "Welcome to the Meal Planner API!"}
