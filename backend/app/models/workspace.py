from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class Workspace(BaseModel):
    __tablename__ = "workspaces"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)

    memberships = relationship("Membership", back_populates="workspace", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="workspace", cascade="all, delete-orphan")

class Membership(BaseModel):
    __tablename__ = "memberships"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member", nullable=False)  # admin, member, viewer

    user = relationship("User", back_populates="memberships")
    workspace = relationship("Workspace", back_populates="memberships")
