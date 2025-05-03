from fastapi import Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from services.social_service import SocialService

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_social_service(db: Session = Depends(get_db)):
    return SocialService(db)

