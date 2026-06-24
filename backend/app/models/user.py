from sqlalchemy import Column, String, Float, ARRAY, JSON, DateTime, func
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=True)   # if using auth later
    username = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    liked_titles = Column(ARRAY(String), default=[])     # list of movie IDs
    disliked_titles = Column(ARRAY(String), default=[])
    preferences = Column(JSON, nullable=True)            # e.g. {"region": ["Korea"], "avoid": ["slow_burn"]}
    taste_vector = Column(ARRAY(Float), nullable=True)   # stored as list of floats (updated periodically)
    created_at = Column(DateTime, server_default=func.now())
