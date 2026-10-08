from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
