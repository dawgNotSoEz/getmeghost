from sqlalchemy import Column, String, Integer, Float, ARRAY, JSON, DateTime, func
from app.core.database import Base
import uuid

class Movie(Base):
    __tablename__ = "movies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tmdb_id = Column(String, unique=True, nullable=True)
    imdb_id = Column(String, unique=True, nullable=True)
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)
    release_year = Column(Integer, nullable=True)
    country = Column(String, nullable=True)
    language = Column(String, nullable=True)          # comma separated if multiple
    runtime = Column(Integer, nullable=True)          # in minutes
    director = Column(String, nullable=True)
    cast = Column(ARRAY(String), nullable=True)
    poster_url = Column(String, nullable=True)
    trailer_url = Column(String, nullable=True)
    rating = Column(Float, nullable=True)             # average user rating (TMDB)
    content_warnings = Column(ARRAY(String), nullable=True)
    genres = Column(ARRAY(String), nullable=True)
    themes = Column(ARRAY(String), nullable=True)
    tone = Column(ARRAY(String), nullable=True)
    style = Column(ARRAY(String), nullable=True)
    tags = Column(ARRAY(String), nullable=True)       # user-facing tags (e.g., "found-footage")
    pacing_score = Column(Float, nullable=True)
    found_footage_score = Column(Float, nullable=True)
    documentary_vibe_score = Column(Float, nullable=True)
    occult_score = Column(Float, nullable=True)
    psychological_score = Column(Float, nullable=True)
    jump_scare_score = Column(Float, nullable=True)
    gore_score = Column(Float, nullable=True)
    novelty_score = Column(Float, nullable=True)

    # Layer 2
    events = Column(ARRAY(String), nullable=True)

    # Layer 3 – numeric dimensions
    ritual_score = Column(Float, nullable=True)
    dread_score = Column(Float, nullable=True)
    documentary_score = Column(Float, nullable=True)
    realism_score = Column(Float, nullable=True)
    slow_burn_score = Column(Float, nullable=True)
    chaos_score = Column(Float, nullable=True)

    # Layer 4
    community_tags = Column(JSON, nullable=True)
    score_confidence = Column(JSON, nullable=True)

    embedding_text = Column(String, nullable=True)    # The rich text that was embedded
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
