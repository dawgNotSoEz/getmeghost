from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, Range, PointRequest, PointStruct, HasIdCondition
from app.core.config import settings
import numpy as np

client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
COLLECTION = "movies"

def get_movie_vector(movie_id: str) -> np.ndarray | None:
    """Retrieve the embedding vector of a movie by its ID."""
    try:
        points = client.retrieve(
            collection_name=COLLECTION,
            ids=[movie_id],
            with_vectors=True
        )
        if points:
            return np.array(points[0].vector)
    except Exception:
        return None
    return None

def get_movie_payload(movie_id: str) -> dict | None:
    """Retrieve the payload (metadata) of a movie by its ID."""
    try:
        points = client.retrieve(
            collection_name=COLLECTION,
            ids=[movie_id],
            with_payload=True,
            with_vectors=False
        )
        if points:
            return points[0].payload
    except Exception:
        return None
    return None

def build_preference_filter(prefs: any) -> Filter | None:
    """Convert user preferences into a Qdrant Filter."""
    if not prefs:
        return None
        
    must_conditions = []
    
    # Support both Pydantic models and dictionaries
    region = getattr(prefs, "region", None) or (prefs.get("region") if isinstance(prefs, dict) else None)
    year_min = getattr(prefs, "year_min", None) or (prefs.get("year_min") if isinstance(prefs, dict) else None)
    year_max = getattr(prefs, "year_max", None) or (prefs.get("year_max") if isinstance(prefs, dict) else None)
    vibe = getattr(prefs, "vibe", None) or (prefs.get("vibe") if isinstance(prefs, dict) else None)
    
    if region:
        must_conditions.append(
            FieldCondition(key="country", match=MatchAny(any=region))
        )
    if year_min or year_max:
        range_kwargs = {}
        if year_min:
            range_kwargs["gte"] = year_min
        if year_max:
            range_kwargs["lte"] = year_max
        if range_kwargs:
            must_conditions.append(
                FieldCondition(key="year", range=Range(**range_kwargs))
            )
    if vibe:
        must_conditions.append(
            FieldCondition(key="tags", match=MatchAny(any=vibe))
        )

    if not must_conditions:
        return None

    return Filter(must=must_conditions)

def get_candidate_movies(
    query_vector: list[float],
    limit: int = 100,
    exclude_ids: list[str] = None,
    prefs_filter: Filter | None = None
) -> list:
    """Query Qdrant for similar movies, applying preferences and excluding rated movies."""
    search_filter = None
    must_not_conditions = []
    
    if exclude_ids:
        must_not_conditions.append(
            HasIdCondition(has_id=exclude_ids)
        )
        
    if prefs_filter:
        search_filter = Filter(
            must=prefs_filter.must if prefs_filter.must else [],
            must_not=must_not_conditions if must_not_conditions else None
        )
    elif must_not_conditions:
        search_filter = Filter(must_not=must_not_conditions)

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=limit,
        with_payload=True,
        with_vectors=False,
        query_filter=search_filter
    )
    
    results = []
    for hit in hits:
        results.append({
            "movie_id": hit.id,
            "similarity_score": hit.score,
            **hit.payload
        })
    return results
