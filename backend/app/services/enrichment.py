import json
import re
from ollama import Client

ollama_client = Client(host="http://localhost:11434")

ENRICHMENT_PROMPT = """
You are a film analyst specialising in horror movies. Given a movie synopsis, extract structured metadata.

Return ONLY a JSON object (no other text) with these fields:

- "themes": array of strings (e.g., ["ritual", "ancestral curse", "burial", "shamanism", "occult"])
- "tone": array of strings (e.g., ["serious", "ominous", "suspenseful", "dreadful"])
- "style": array of strings (e.g., ["investigation", "slow escalation", "ritual scenes", "atmospheric"])
- "tags": array of strings (e.g., ["modern", "asian", "cursed", "folklore", "dread", "found-footage"])
- "pacing_score": number from 1 (very slow) to 10 (fast-paced)
- "occult_score": number from 1 to 10 (how much occult/ritual)
- "psychological_score": number from 1 to 10
- "jump_scare_score": number from 1 to 10
- "gore_score": number from 1 to 10
- "found_footage_score": number from 1 to 10
- "documentary_vibe_score": number from 1 to 10
- "novelty_score": number from 1 to 10 (how unique/original)
- "embedding_text": a single string (500-800 characters) that summarises the movie in a way that captures its vibe, themes, style, and emotional effect. Use a descriptive, natural paragraph. Include comparable titles if possible.

Synopsis: "{synopsis}"
"""

def extract_metadata(synopsis: str) -> dict:
    response = ollama_client.generate(
        model="mistral",
        prompt=ENRICHMENT_PROMPT.format(synopsis=synopsis),
        format="json",   # enforce JSON output (requires recent Ollama)
        options={"temperature": 0.1}
    )
    try:
        metadata = json.loads(response["response"])
        return metadata
    except json.JSONDecodeError:
        # fallback: try to extract JSON from the response
        json_match = re.search(r"\{.*\}", response["response"], re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError("Failed to parse LLM output as JSON")
