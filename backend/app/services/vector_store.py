from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings

client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

COLLECTION_NAME = "movies"

def ensure_collection():
    collections = client.get_collections().collections
    if COLLECTION_NAME not in [c.name for c in collections]:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)  # MiniLM-L6-v2 dim = 384
        )

def upsert_movie_vector(movie_id: str, vector: list[float], payload: dict):
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=movie_id,
                vector=vector,
                payload=payload
            )
        ]
    )
