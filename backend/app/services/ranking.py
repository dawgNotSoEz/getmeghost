import numpy as np
from .movie_service import get_movie_vector, client as qdrant_client

COLLECTION = "movies"

def compute_dislike_penalty(candidate_vector: np.ndarray, disliked_ids: list[str]) -> float:
    """Return a penalty proportional to the average cosine similarity to disliked movies."""
    if not disliked_ids:
        return 0.0
    similarities = []
    for mid in disliked_ids:
        vec = get_movie_vector(mid)
        if vec is not None:
            sim = np.dot(candidate_vector, vec) / (np.linalg.norm(candidate_vector) * np.linalg.norm(vec) + 1e-9)
            similarities.append(sim)
    if not similarities:
        return 0.0
    avg_sim = np.mean(similarities)
    # Map similarity (0 to 1) to penalty (0 to 0.5). So high similarity to disliked yields high penalty.
    return float(avg_sim * 0.5)

def compute_constraint_match(candidate_payload: dict, prefs: any) -> float:
    """How well does the candidate match explicit preferences (vibe/tags overlap)."""
    score = 0.0
    vibe = getattr(prefs, "vibe", None) or (prefs.get("vibe") if isinstance(prefs, dict) else None)
    if vibe:
        candidate_tags = set(candidate_payload.get("tags", []))
        wanted_tags = set(vibe)
        overlap = len(candidate_tags & wanted_tags)
        if wanted_tags and overlap > 0:
            score += overlap / len(wanted_tags)  # max 1.0
    return score

def compute_quality_score(candidate_payload: dict) -> float:
    """Use rating (0-10) scaled to 0-1. If missing, assume 0.5."""
    rating = candidate_payload.get("rating")
    # Also support "quality_score" or avg rating if mapped
    if rating is None:
        return 0.5
    return rating / 10.0

def compute_novelty(candidate_payload: dict) -> float:
    """Use novelty_score from enrichment (1-10) scaled to 0-1, else default 0.5."""
    score = candidate_payload.get("novelty_score")
    if score is None:
        return 0.5
    return score / 10.0

def rank_candidates(
    candidates: list[dict],
    disliked_ids: list[str],
    prefs: any,
    weight_semantic: float = 0.30,
    weight_constraint: float = 0.20,
    weight_penalty: float = 0.15,
    weight_quality: float = 0.10,
    weight_novelty: float = 0.10,
) -> list[dict]:
    """
    Takes raw candidates (with similarity_score), scores each, returns sorted list.
    """
    scored = []
    for c in candidates:
        candidate_vector = get_movie_vector(c["movie_id"])
        if candidate_vector is None:
            continue

        semantic = c["similarity_score"]  # cosine similarity from Qdrant

        constraint = compute_constraint_match(c, prefs)
        penalty = compute_dislike_penalty(candidate_vector, disliked_ids)
        quality = compute_quality_score(c)
        novelty = compute_novelty(c)

        final = (
            weight_semantic * semantic
            + weight_constraint * constraint
            + weight_quality * quality
            + weight_novelty * novelty
            - weight_penalty * penalty
        )

        scored.append({
            **c,
            "final_score": round(final, 4),
            "penalty": round(penalty, 4),
            "constraint_match": round(constraint, 4),
        })

    # Sort by final_score descending
    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored

def mmr_rerank(
    candidates: list[dict],
    lambda_param: float = 0.7,
    top_k: int = 20,
) -> list[dict]:
    """
    Greedy MMR re-ranking to balance relevance and diversity.
    `lambda_param` controls relevance vs diversity tradeoff.
    1 = pure relevance, 0 = pure diversity.
    """
    if not candidates:
        return []

    # We'll need vectors for all candidates
    vectors = {}
    for c in candidates:
        vec = get_movie_vector(c["movie_id"])
        if vec is not None:
            vectors[c["movie_id"]] = vec

    selected = []
    remaining = candidates.copy()

    # First pick the best scored
    best = remaining.pop(0)
    selected.append(best)

    while len(selected) < top_k and remaining:
        mmr_scores = []
        for c in remaining:
            relevance = c["final_score"]
            # Max similarity to any already selected
            if c["movie_id"] not in vectors:
                sim_max = 0.5  # fallback
            else:
                sims = [
                    np.dot(vectors[c["movie_id"]], vectors[s["movie_id"]]) /
                    (np.linalg.norm(vectors[c["movie_id"]]) * np.linalg.norm(vectors[s["movie_id"]]) + 1e-9)
                    for s in selected if s["movie_id"] in vectors
                ]
                sim_max = max(sims) if sims else 0.0

            mmr = lambda_param * relevance - (1 - lambda_param) * sim_max
            mmr_scores.append(mmr)
        # Pick the remaining candidate with highest MMR
        best_idx = np.argmax(mmr_scores)
        selected.append(remaining.pop(int(best_idx)))

    return selected
