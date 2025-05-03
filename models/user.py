from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    profile_picture = Column(String, nullable=True)

    posts = relationship("Post", back_populates="user", cascade="all, delete")
    # likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    # comments = relationship("Comment", back_populates="user", cascade="all, delete")
