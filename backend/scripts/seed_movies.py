import asyncio
import json
import sys
import os

# Ensure the parent directory is in sys.path if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session
from app.models.movie import Movie
from app.services.enrichment_v2 import enrich_movie
from app.services.embedding import generate_embedding
from app.services.vector_store import ensure_collection, upsert_movie_vector
from sqlalchemy import select

async def seed_movies(json_path: str):
    with open(json_path) as f:
        movies_data = json.load(f)

    ensure_collection()

    async with async_session() as session:
        for movie_dict in movies_data:
            # Check if already exists by tmdb_id
            existing = await session.execute(
                select(Movie).where(Movie.tmdb_id == movie_dict["tmdb_id"])
            )
            if existing.scalar_one_or_none():
                print(f"Skipping {movie_dict['title']} (already exists)")
                continue

            # Enrich with new two-stage pipeline
            print(f"Enriching {movie_dict['title']}...")
            enrichment = enrich_movie(movie_id=None, synopsis=movie_dict["synopsis"])

            # Build embedding text from extracted events and metadata
            embed_text = (
                f"Title: {movie_dict['title']}. "
                f"Country: {movie_dict.get('country')}. "
                f"Year: {movie_dict.get('release_year')}. "
                f"Events: {', '.join(enrichment.get('events', []))}. "
                f"Synopsis: {movie_dict['synopsis']}"
            )

            # Generate vector
            vector = generate_embedding(embed_text)

            # Create DB record
            db_movie = Movie(
                tmdb_id=movie_dict["tmdb_id"],
                title=movie_dict["title"],
                original_title=movie_dict.get("original_title"),
                release_year=movie_dict.get("release_year"),
                country=movie_dict.get("country"),
                language=movie_dict.get("language"),
                runtime=movie_dict.get("runtime"),
                director=movie_dict.get("director"),
                cast=movie_dict.get("cast"),
                genres=movie_dict.get("genres"),
                events=enrichment.get("events", []),
                ritual_score=enrichment.get("ritual_score"),
                dread_score=enrichment.get("dread_score"),
                documentary_score=enrichment.get("documentary_score"),
                realism_score=enrichment.get("realism_score"),
                slow_burn_score=enrichment.get("slow_burn_score"),
                chaos_score=enrichment.get("chaos_score"),
                occult_score=enrichment.get("occult_score"),
                psychological_score=enrichment.get("psychological_score"),
                jump_scare_score=enrichment.get("jump_scare_score"),
                gore_score=enrichment.get("gore_score"),
                found_footage_score=enrichment.get("documentary_score"),
                documentary_vibe_score=enrichment.get("documentary_score"),
                pacing_score=None,
                novelty_score=enrichment.get("novelty_score"),
                score_confidence=enrichment.get("score_confidence", {}),
                tags=enrichment.get("events", []),  # map events as tags for explanations
                embedding_text=embed_text,
            )
            session.add(db_movie)
            await session.commit()
            await session.refresh(db_movie)

            # Upsert to Qdrant with all new numeric scores
            payload = {
                "title": movie_dict["title"],
                "year": movie_dict.get("release_year"),
                "country": movie_dict.get("country"),
                "genres": movie_dict.get("genres"),
                "tags": enrichment.get("events", []),
                "events": enrichment.get("events", []),
                "ritual_score": enrichment.get("ritual_score"),
                "dread_score": enrichment.get("dread_score"),
                "documentary_score": enrichment.get("documentary_score"),
                "realism_score": enrichment.get("realism_score"),
                "slow_burn_score": enrichment.get("slow_burn_score"),
                "chaos_score": enrichment.get("chaos_score"),
                "occult_score": enrichment.get("occult_score"),
                "psychological_score": enrichment.get("psychological_score"),
                "jump_scare_score": enrichment.get("jump_scare_score"),
                "gore_score": enrichment.get("gore_score"),
                "novelty_score": enrichment.get("novelty_score"),
                "score_confidence": enrichment.get("score_confidence", {}),
            }
            upsert_movie_vector(movie_id=db_movie.id, vector=vector, payload=payload)
            print(f"Added {movie_dict['title']} to DB and Qdrant")

if __name__ == "__main__":
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "../seed_data/movies.json")
    asyncio.run(seed_movies(json_path))
