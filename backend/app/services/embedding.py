from sentence_transformers import SentenceTransformer
from app.core.config import settings

model = SentenceTransformer(settings.embedding_model)   # downloads on first run

def generate_embedding(text: str) -> list[float]:
    return model.encode(text).tolist()
