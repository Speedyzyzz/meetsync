from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class Attendee(BaseModel):
    __tablename__ = "attendees"

    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    display_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)

    meeting = relationship("Meeting", back_populates="attendees")
