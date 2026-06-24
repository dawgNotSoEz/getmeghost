from pydantic import BaseModel, Field
from typing import List, Optional

class UserPreferences(BaseModel):
    region: Optional[List[str]] = None      # e.g., ["Korea", "Japan"]
    vibe: Optional[List[str]] = None        # e.g., ["ritual", "occult"]
    avoid: Optional[List[str]] = None       # e.g., ["slow-burn", "family drama"]
    year_min: Optional[int] = None
    year_max: Optional[int] = None

class TasteSubmission(BaseModel):
    liked: List[str] = Field(default_factory=list)
    disliked: List[str] = Field(default_factory=list)
    preferences: UserPreferences = Field(default_factory=UserPreferences)

class RecommendationItem(BaseModel):
    movie_id: str
    title: str
    year: Optional[int]
    country: Optional[str]
    genres: Optional[List[str]]
    similarity_score: float
    final_score: float
    why: List[str] = []
    warnings: List[str] = []

class RecommendationResponse(BaseModel):
    results: List[RecommendationItem]
