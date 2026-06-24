import json
import re
from typing import List, Dict, Optional
from ollama import Client
from app.core.config import settings

client = Client(host="http://localhost:11434")

# List of dimensions we want scores for
DIMENSIONS = [
    "ritual_score",
    "occult_score",
    "documentary_score",
    "realism_score",
    "slow_burn_score",
    "chaos_score",
    "jump_scare_score",
    "gore_score",
    "psychological_score",
    "dread_score",
    "novelty_score"
]

def extract_events(synopsis: str) -> List[str]:
    """
    Use Ollama to list objective events from the synopsis.
    """
    prompt = f"""
You are a film analyst. Based ONLY on the provided synopsis, list every concrete event or narrative element that occurs in the movie.
Use short, descriptive phrases (e.g., "grave excavation", "shamanic ritual", "police investigation", "documentary crew filming").
Return ONLY a JSON object with key "events" containing an array of strings. Do not add any explanation.

Synopsis: "{synopsis}"
"""
    resp = client.generate(model="qwen2.5:1.5b", prompt=prompt, format="json", options={"temperature": 0.1})
    try:
        data = json.loads(resp["response"])
        return data.get("events", [])
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", resp["response"], re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data.get("events", [])
        return []

def score_from_events_and_synopsis(events: List[str], synopsis: str) -> Dict[str, Dict[str, float]]:
    """
    Given events and synopsis, ask LLM to rate each dimension on a 1-10 scale,
    and provide a confidence (0-1) for each rating.
    If there is absolutely no evidence for a dimension, set its value to null and confidence to 0.0.
    """
    events_str = ", ".join(events)
    prompt = f"""
You are a horror film analyst. You have the following list of concrete events from a movie:
{events_str}

Additional context (synopsis): "{synopsis}"

For each of the following dimensions, rate the movie on a scale from 1 to 10 (1 = barely present, 10 = extremely prominent).
If there is absolutely no evidence in the events or synopsis for a dimension, set its "value" to null and "confidence" to 0.0.
Also, provide a confidence score (0.0 to 1.0) for each rating, reflecting how certain you are based on the available information.

Return ONLY a JSON object with this exact structure (no other text):
{{
  "ritual_score": {{"value": null, "confidence": 0.0}},
  "occult_score": {{"value": 8, "confidence": 0.9}},
  "documentary_score": {{"value": null, "confidence": 0.0}},
  "realism_score": {{"value": 5, "confidence": 0.8}},
  "slow_burn_score": {{"value": null, "confidence": 0.0}},
  "chaos_score": {{"value": null, "confidence": 0.0}},
  "jump_scare_score": {{"value": null, "confidence": 0.0}},
  "gore_score": {{"value": null, "confidence": 0.0}},
  "psychological_score": {{"value": null, "confidence": 0.0}},
  "dread_score": {{"value": null, "confidence": 0.0}},
  "novelty_score": {{"value": 5, "confidence": 0.8}}
}}
"""
    resp = client.generate(model="qwen2.5:1.5b", prompt=prompt, format="json", options={"temperature": 0.1})
    try:
        return json.loads(resp["response"])
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", resp["response"], re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}

def enrich_movie(movie_id: str, synopsis: str) -> dict:
    """
    Full enrichment: extract events, then get scored dimensions with confidence.
    Returns a dictionary ready to be merged into a Movie record.
    """
    events = extract_events(synopsis)
    scored = score_from_events_and_synopsis(events, synopsis)

    # Flatten into simple fields
    result = {"events": events}
    confidence_dict = {}
    for dim in DIMENSIONS:
        data = scored.get(dim)
        if isinstance(data, dict):
            val = data.get("value")
            # If value is none or not present, set to None
            result[dim] = val if val is not None else None
            confidence_dict[dim] = data.get("confidence", 0.0) if val is not None else 0.0
        else:
            # Fallback if structure is flat or not a dict
            result[dim] = None
            confidence_dict[dim] = 0.0
            
    result["score_confidence"] = confidence_dict
    return result
