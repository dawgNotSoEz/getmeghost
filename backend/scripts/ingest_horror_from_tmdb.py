import asyncio
import json
import sys
import os
import time
import requests

# Ensure the parent directory is in sys.path if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import async_session
from app.models.movie import Movie
from app.services.enrichment_v2 import enrich_movie
from app.services.embedding import generate_embedding
from app.services.vector_store import ensure_collection, upsert_movie_vector
from sqlalchemy import select

# Curated fallback catalog of 15 famous horror films for immediate keyless ingestion
FALLBACK_MOVIES = [
    {
        "tmdb_id": "503",
        "title": "The Ring",
        "release_year": 2002,
        "country": "United States",
        "language": "English",
        "runtime": 115,
        "director": "Gore Verbinski",
        "cast": ["Naomi Watts", "Martin Henderson", "David Dorfman", "Brian Cox"],
        "genres": ["Horror", "Mystery"],
        "synopsis": "A young journalist investigates a cursed videotape that seems to cause the death of anyone who watches it within a week."
    },
    {
        "tmdb_id": "11037",
        "title": "A Tale of Two Sisters",
        "release_year": 2003,
        "country": "South Korea",
        "language": "Korean",
        "runtime": 114,
        "director": "Kim Jee-woon",
        "cast": ["Im Soo-jung", "Moon Geun-young", "Yum Jung-ah", "Kim Kap-soo"],
        "genres": ["Horror", "Drama", "Mystery", "Thriller"],
        "synopsis": "Two sisters return home from a mental institution to face a cruel stepmother and a ghost haunting their house."
    },
    {
        "tmdb_id": "11082",
        "title": "Shutter",
        "release_year": 2004,
        "country": "Thailand",
        "language": "Thai",
        "runtime": 97,
        "director": "Banjong Pisanthanakun",
        "cast": ["Ananda Everingham", "Natthaweeranuch Thongmee", "Achita Sikamana"],
        "genres": ["Horror", "Mystery"],
        "synopsis": "A young photographer and his girlfriend discover mysterious shadows in their photographs after a hit-and-run accident."
    },
    {
        "tmdb_id": "21262",
        "title": "Noroi: The Curse",
        "release_year": 2005,
        "country": "Japan",
        "language": "Japanese",
        "runtime": 115,
        "director": "Koji Shiraishi",
        "cast": ["Jin Muraki", "Rio Kanno", "Tomono Kuga", "Marika Matsumoto"],
        "genres": ["Horror", "Mystery"],
        "synopsis": "A documentary filmmaker goes missing while investigating a series of bizarre paranormal events related to an ancient demonic ritual."
    },
    {
        "tmdb_id": "19833",
        "title": "R-Point",
        "release_year": 2004,
        "country": "South Korea",
        "language": "Korean",
        "runtime": 107,
        "director": "Kong Su-chang",
        "cast": ["Kam Woo-sung", "Son Byong-ho", "Oh Tae-kyung", "Park Won-sang"],
        "genres": ["Horror", "Mystery", "War", "Thriller"],
        "synopsis": "During the Vietnam War, a South Korean military squad is sent to find a missing platoon on a haunted island called R-Point."
    },
    {
        "tmdb_id": "138843",
        "title": "The Conjuring",
        "release_year": 2013,
        "country": "United States",
        "language": "English",
        "runtime": 112,
        "director": "James Wan",
        "cast": ["Vera Farmiga", "Patrick Wilson", "Lili Taylor", "Ron Livingston"],
        "genres": ["Horror", "Mystery", "Thriller"],
        "synopsis": "Paranormal investigators Ed and Lorraine Warren work to help a family terrorized by a dark presence in their farmhouse."
    },
    {
        "tmdb_id": "58048",
        "title": "Insidious",
        "release_year": 2010,
        "country": "United States",
        "language": "English",
        "runtime": 103,
        "director": "James Wan",
        "cast": ["Patrick Wilson", "Rose Byrne", "Ty Simpkins", "Lin Shaye"],
        "genres": ["Horror", "Thriller"],
        "synopsis": "A family looks to prevent evil spirits from trapping their comatose child in a realm called The Further."
    },
    {
        "tmdb_id": "82507",
        "title": "Sinister",
        "release_year": 2012,
        "country": "United States",
        "language": "English",
        "runtime": 110,
        "director": "Scott Derrickson",
        "cast": ["Ethan Hawke", "Juliet Rylance", "Fred Thompson", "James Ransone"],
        "genres": ["Horror", "Mystery", "Thriller"],
        "synopsis": "A true-crime writer finds a box of disturbing home movies in his new house that suggest a supernatural presence."
    },
    {
        "tmdb_id": "270303",
        "title": "It Follows",
        "release_year": 2014,
        "country": "United States",
        "language": "English",
        "runtime": 100,
        "director": "David Robert Mitchell",
        "cast": ["Maika Monroe", "Keir Gilchrist", "Daniel Zovatto", "Jake Weary"],
        "genres": ["Horror", "Mystery", "Thriller"],
        "synopsis": "A young woman is followed by an unknown supernatural force after a sexual encounter, and must pass the curse to someone else."
    },
    {
        "tmdb_id": "530385",
        "title": "Midsommar",
        "release_year": 2019,
        "country": "United States",
        "language": "English",
        "runtime": 148,
        "director": "Ari Aster",
        "cast": ["Florence Pugh", "Jack Reynor", "William Jackson Harper", "Vilhelm Blomgren"],
        "genres": ["Horror", "Drama", "Mystery"],
        "synopsis": "A couple travels to Scandinavia to visit a rural hometown's fabled Swedish midsummer festival, which turns into a pagan cult ritual."
    },
    {
        "tmdb_id": "760104",
        "title": "The Medium",
        "release_year": 2021,
        "country": "Thailand",
        "language": "Thai",
        "runtime": 130,
        "director": "Banjong Pisanthanakun",
        "cast": ["Narilya Gulmongkolpech", "Sawanee Utoomma", "Sirani Yankittikan"],
        "genres": ["Horror"],
        "synopsis": "A documentary crew follows a shaman in northeast Thailand whose niece is possessed by a terrifying entity."
    },
    {
        "tmdb_id": "477610",
        "title": "Satan's Slaves",
        "release_year": 2017,
        "country": "Indonesia",
        "language": "Indonesian",
        "runtime": 107,
        "director": "Joko Anwar",
        "cast": ["Tara Basro", "Bront Palarae", "Dimas Aditya", "Endy Arfian"],
        "genres": ["Horror", "Mystery", "Thriller"],
        "synopsis": "After a mother dies from a mysterious illness, her family is haunted by her ghost, uncovering a deal she made with a satanic cult."
    },
    {
        "tmdb_id": "614458",
        "title": "Impetigore",
        "release_year": 2019,
        "country": "Indonesia",
        "language": "Indonesian",
        "runtime": 106,
        "director": "Joko Anwar",
        "cast": ["Tara Basro", "Ario Bayu", "Marissa Anita", "Christine Hakim"],
        "genres": ["Horror", "Mystery", "Thriller"],
        "synopsis": "A young woman returns to her ancestral village to claim an inheritance, only to find the villagers trying to kill her to lift a curse."
    },
    {
        "tmdb_id": "11410",
        "title": "Pulse",
        "release_year": 2001,
        "country": "Japan",
        "language": "Japanese",
        "runtime": 119,
        "director": "Kiyoshi Kurosawa",
        "cast": ["Haruhiko Kato", "Kumiko Aso", "Koyuki", "Kurume Arisaka"],
        "genres": ["Horror", "Mystery", "Science Fiction"],
        "synopsis": "Two groups of people discover evidence that spirits are trying to invade the human world through the internet."
    },
    {
        "tmdb_id": "10986",
        "title": "Dark Water",
        "release_year": 2002,
        "country": "Japan",
        "language": "Japanese",
        "runtime": 101,
        "director": "Hideo Nakata",
        "cast": ["Hitomi Kuroki", "Rio Kanno", "Shingo Mitsumori", "Asami Mizukawa"],
        "genres": ["Horror", "Drama", "Mystery", "Thriller"],
        "synopsis": "A divorced mother and her daughter move into a decaying apartment building haunted by the spirit of a missing girl."
    }
]

def fetch_from_tmdb(api_key: str, max_movies: int = 100) -> list:
    """
    Fetch popular horror movies from TMDB API.
    """
    print(f"Connecting to TMDB API to fetch up to {max_movies} horror movies...")
    base_url = "https://api.themoviedb.org/3"
    movies = []
    page = 1
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    consecutive_failures = 0
    
    # TMDB horror genre ID is 27
    while len(movies) < max_movies:
        discover_url = f"{base_url}/discover/movie"
        params = {
            "api_key": api_key,
            "with_genres": "27",
            "sort_by": "popularity.desc",
            "page": page,
            "include_adult": "false"
        }
        
        try:
            resp = requests.get(discover_url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error fetching discover page {page}: {e}")
            break
            
        results = data.get("results", [])
        if not results:
            break
            
        for m in results:
            if len(movies) >= max_movies:
                break
                
            tmdb_id = str(m["id"])
            print(f"Fetching details for TMDB ID {tmdb_id}: {m['title']}...")
            
            # Fetch full details
            detail_url = f"{base_url}/movie/{tmdb_id}"
            credits_url = f"{base_url}/movie/{tmdb_id}/credits"
            
            try:
                # 1. Movie details
                d_resp = requests.get(detail_url, params={"api_key": api_key}, headers=headers, timeout=10)
                d_resp.raise_for_status()
                detail = d_resp.json()
                
                # 2. Credits (cast/crew)
                c_resp = requests.get(credits_url, params={"api_key": api_key}, headers=headers, timeout=10)
                c_resp.raise_for_status()
                credits = c_resp.json()
                
                # Parse fields
                countries = [c["name"] for c in detail.get("production_countries", [])]
                country = countries[0] if countries else "Unknown"
                
                genres = [g["name"] for g in detail.get("genres", [])]
                
                cast = [actor["name"] for actor in credits.get("cast", [])[:5]]
                
                director = None
                for crew_member in credits.get("crew", []):
                    if crew_member.get("job") == "Director":
                        director = crew_member.get("name")
                        break
                
                release_year = None
                release_date = detail.get("release_date")
                if release_date:
                    release_year = int(release_date.split("-")[0])
                
                movies.append({
                    "tmdb_id": tmdb_id,
                    "title": detail.get("title"),
                    "original_title": detail.get("original_title"),
                    "release_year": release_year,
                    "country": country,
                    "language": detail.get("original_language"),
                    "runtime": detail.get("runtime"),
                    "director": director,
                    "cast": cast,
                    "genres": genres,
                    "synopsis": detail.get("overview")
                })
                
                consecutive_failures = 0
                # Sleep briefly to respect free tier rate limit
                time.sleep(0.25)
                
            except Exception as e:
                print(f"Error fetching movie {tmdb_id} details: {e}")
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print("Too many consecutive errors fetching details from TMDB (network/ISP block). Aborting TMDB fetch.")
                    return movies
                time.sleep(0.5)
                continue
                
        page += 1
        
    return movies

async def ingest_catalog(max_movies: int = 100):
    ensure_collection()
    
    api_key = settings.tmdb_api_key
    movies_to_ingest = []
    if not api_key:
        print("WARNING: No TMDB_API_KEY found in .env config. Appending curated fallback horror catalog instead.")
        movies_to_ingest = FALLBACK_MOVIES
    else:
        try:
            movies_to_ingest = fetch_from_tmdb(api_key, max_movies)
        except Exception as e:
            print(f"Error fetching from TMDB: {e}. Falling back to curated catalog.")
            movies_to_ingest = FALLBACK_MOVIES

    if not movies_to_ingest:
        print("WARNING: Ingestion fetched 0 movies from TMDB or hit a network block. Falling back to curated catalog.")
        movies_to_ingest = FALLBACK_MOVIES

    print(f"Beginning ingestion pipeline for {len(movies_to_ingest)} horror movies...")
    
    async with async_session() as session:
        for idx, movie_dict in enumerate(movies_to_ingest):
            # Check if movie already exists by tmdb_id
            existing = await session.execute(
                select(Movie).where(Movie.tmdb_id == movie_dict["tmdb_id"])
            )
            if existing.scalar_one_or_none():
                print(f"[{idx+1}/{len(movies_to_ingest)}] Skipping {movie_dict['title']} (already exists)")
                continue
                
            print(f"[{idx+1}/{len(movies_to_ingest)}] Ingesting & Enriching: {movie_dict['title']}...")
            
            # Enrich movie using two-stage pipeline
            try:
                enrichment = enrich_movie(movie_id=None, synopsis=movie_dict["synopsis"])
            except Exception as e:
                print(f"Enrichment failed for {movie_dict['title']}: {e}. Skipping.")
                continue

            # Build embedding text from facts + events
            embed_text = (
                f"Title: {movie_dict['title']}. "
                f"Country: {movie_dict.get('country')}. "
                f"Year: {movie_dict.get('release_year')}. "
                f"Events: {', '.join(enrichment.get('events', []))}. "
                f"Synopsis: {movie_dict['synopsis']}"
            )
            
            # Generate embedding
            try:
                vector = generate_embedding(embed_text)
            except Exception as e:
                print(f"Embedding generation failed for {movie_dict['title']}: {e}. Skipping.")
                continue

            # Create database record
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
                tags=enrichment.get("events", []),  # map events as explanation tags
                embedding_text=embed_text,
            )
            
            session.add(db_movie)
            await session.commit()
            await session.refresh(db_movie)
            
            # Upsert movie vector and numeric fields to Qdrant
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
            print(f"Successfully added {movie_dict['title']} to DB and Qdrant.")
            
    print("Ingestion pipeline finished successfully!")

if __name__ == "__main__":
    max_movies = 50
    if len(sys.argv) > 1:
        try:
            max_movies = int(sys.argv[1])
        except ValueError:
            pass
            
    asyncio.run(ingest_catalog(max_movies))
