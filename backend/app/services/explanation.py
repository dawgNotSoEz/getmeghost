from .movie_service import get_movie_payload

def generate_explanation(candidate: dict, liked_ids: list[str], prefs: any) -> tuple[list[str], list[str]]:
    """
    Return (why, warnings) lists of natural language strings.
    """
    why = []
    warnings = []

    payload = candidate  # already contains tags, themes, etc.
    candidate_tags = set(payload.get("tags", []))

    # Extract preferences fields dynamically supporting both dictionary and object
    region = getattr(prefs, "region", None) or (prefs.get("region") if isinstance(prefs, dict) else None)
    vibe = getattr(prefs, "vibe", None) or (prefs.get("vibe") if isinstance(prefs, dict) else None)
    avoid = getattr(prefs, "avoid", None) or (prefs.get("avoid") if isinstance(prefs, dict) else None)

    # 1. Match with liked movie tags
    if liked_ids:
        liked_tags = set()
        for mid in liked_ids[:5]:  # sample a few
            lp = get_movie_payload(mid)
            if lp:
                liked_tags.update(lp.get("tags", []))
        overlap = candidate_tags & liked_tags
        if overlap:
            why.append(f"Shares tags with movies you loved: {', '.join(sorted(overlap)[:4])}")

    # 2. Match with explicit vibe preferences
    if vibe:
        vibe_overlap = candidate_tags & set(vibe)
        if vibe_overlap:
            why.append(f"Matches your preferred vibe: {', '.join(sorted(vibe_overlap))}")

    # 3. Region match
    if region and candidate.get("country") in region:
        why.append(f"From your selected region: {candidate['country']}")

    # 4. Constraint satisfaction general
    if avoid:
        avoid_tags = set(avoid)
        hit_avoid = candidate_tags & avoid_tags
        if hit_avoid:
            warnings.append(f"Contains tags you wanted to avoid: {', '.join(hit_avoid)}")
        else:
            why.append("Avoids all your negative preferences")

    # 5. High occult/psychological intensity if that's the vibe
    occult = candidate.get("occult_score", 0)
    if occult and occult > 7:
        why.append(f"Strong occult/ritual elements (intensity {occult}/10)")

    psych = candidate.get("psychological_score", 0)
    if psych and psych > 7:
        why.append(f"High psychological tension (intensity {psych}/10)")

    return why, warnings
