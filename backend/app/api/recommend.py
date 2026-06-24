from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.core.database import async_session
from app.models.movie import Movie
from app.schemas.taste import TasteSubmission, RecommendationResponse, RecommendationItem
from app.services.taste_service import build_taste_vector
from app.services.movie_service import get_candidate_movies, build_preference_filter
from app.services.ranking import rank_candidates, mmr_rerank
from app.services.explanation import generate_explanation

router = APIRouter()

@router.get("/movies")
async def get_movies():
    async with async_session() as session:
        result = await session.execute(select(Movie))
        movies = result.scalars().all()
        return [
            {
                "id": m.id,
                "title": m.title,
                "year": m.release_year,
                "country": m.country,
                "genres": m.genres or [],
                "director": m.director
            }
            for m in movies
        ]

@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(taste: TasteSubmission):
    # Build taste vector
    taste_vector = build_taste_vector(taste.liked, taste.disliked)
    if taste_vector is None:
        raise HTTPException(status_code=400, detail="No valid movies provided in liked/disliked lists.")

    # Build filter from preferences
    prefs_filter = build_preference_filter(taste.preferences)

    # Retrieve candidates (top 100)
    exclude_ids = list(set(taste.liked + taste.disliked))
    raw_candidates = get_candidate_movies(
        query_vector=taste_vector.tolist(),
        limit=100,
        exclude_ids=exclude_ids,
        prefs_filter=prefs_filter
    )

    if not raw_candidates:
        return RecommendationResponse(results=[])

    # Rank with multi-factor scoring
    scored = rank_candidates(
        candidates=raw_candidates,
        disliked_ids=taste.disliked,
        prefs=taste.preferences
    )

    # Diversity re-ranking (top 20 final)
    diverse = mmr_rerank(scored, lambda_param=0.7, top_k=20)

    # Generate explanations
    final_results = []
    for movie in diverse:
        why, warnings = generate_explanation(
            movie,
            taste.liked,
            taste.preferences
        )
        final_results.append(RecommendationItem(
            movie_id=movie["movie_id"],
            title=movie.get("title", "Unknown"),
            year=movie.get("year"),
            country=movie.get("country"),
            genres=movie.get("genres", []),
            similarity_score=movie["similarity_score"],
            final_score=movie["final_score"],
            why=why,
            warnings=warnings
        ))

    return RecommendationResponse(results=final_results)
