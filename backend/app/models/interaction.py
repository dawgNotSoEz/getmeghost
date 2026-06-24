from sqlalchemy import Column, String, Float, DateTime, Enum, func
from app.core.database import Base
import uuid
import enum

class InteractionEvent(enum.Enum):
    SEARCHED = "searched"
    CLICKED = "clicked"
    WATCHED_TRAILER = "watched_trailer"
    SAVED = "saved"
    SKIPPED = "skipped"
    LIKED = "liked"
    DISLIKED = "disliked"
    SHARED = "shared"
    WATCH_COMPLETE = "watch_complete"
    WATCH_ABANDONED = "watch_abandoned"

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    movie_id = Column(String, nullable=False)
    event = Column(Enum(InteractionEvent), nullable=False)
    value = Column(Float, nullable=True)   # optional weight (e.g., watch duration)
    timestamp = Column(DateTime, server_default=func.now())
