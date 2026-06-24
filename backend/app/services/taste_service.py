import numpy as np
from .movie_service import get_movie_vector

def build_taste_vector(
    liked_ids: list[str],
    disliked_ids: list[str],
    like_weight: float = 0.6,
    dislike_weight: float = 0.4
) -> np.ndarray | None:
    """
    Compute the user taste vector as a weighted combination:
    taste = (like_weight * mean(liked_vectors)) - (dislike_weight * mean(disliked_vectors))
    If neither liked nor disliked vectors are available, return None.
    """
    liked_vectors = []
    for mid in liked_ids:
        vec = get_movie_vector(mid)
        if vec is not None:
            liked_vectors.append(vec)

    disliked_vectors = []
    for mid in disliked_ids:
        vec = get_movie_vector(mid)
        if vec is not None:
            disliked_vectors.append(vec)

    if not liked_vectors and not disliked_vectors:
        return None

    # Compute means
    liked_mean = np.mean(liked_vectors, axis=0) if liked_vectors else np.zeros(384)
    disliked_mean = np.mean(disliked_vectors, axis=0) if disliked_vectors else np.zeros(384)

    taste_vector = like_weight * liked_mean - dislike_weight * disliked_mean
    # Normalize to unit length (cosine similarity expects normalized vectors)
    norm = np.linalg.norm(taste_vector)
    if norm > 0:
        taste_vector = taste_vector / norm
    return taste_vector
