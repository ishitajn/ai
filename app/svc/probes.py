from typing import List, Dict, Tuple
from app.schemas import Message, FeatureProbes
import numpy as np
import asyncio

# In-memory cache for feature probes
probe_cache: Dict[Tuple[str, ...], FeatureProbes] = {}

# Keyword lists for various detectors
GREETING_KEYWORDS = {"hello", "hi", "hey", "yo", "sup"}
FLIRT_KEYWORDS = {"wink", "cute", "crush", ";)", ":-)", "beautiful"}
DISCLOSURE_KEYWORDS = {"i think", "i feel", "my favorite", "i love", "i am"}
LOCATION_KEYWORDS = {"here", "there", "place", "city", "country", "home", "area"}

async def evaluate(turns: List[Message], vecs: np.ndarray) -> FeatureProbes:
    """
    Computes feature probes, with an added caching layer to improve performance.
    """
    # 1. Create a hashable key from the conversation turns' text content.
    cache_key = tuple(t.text for t in turns)
    if cache_key in probe_cache:
        return probe_cache[cache_key]

    # This is an async function, so we must await something to yield control.
    await asyncio.sleep(0)

    features = FeatureProbes()
    if not turns:
        return features

    last_turn = turns[-1]
    last_text_lower = last_turn.text.lower()

    # --- The rest of the evaluation logic is the same ---
    features.last_response_by = last_turn.role
    if any(word in last_text_lower for word in GREETING_KEYWORDS): features.greetings = True
    if '?' in last_text_lower: features.questions = True
    if any(word in last_text_lower for word in FLIRT_KEYWORDS):
        features.flirtation_detected = True
        features.playful_energy = True
    if any(word in last_text_lower for word in LOCATION_KEYWORDS): features.location_related = True
    for turn in turns[-3:]:
        if any(word in turn.text.lower() for word in GREETING_KEYWORDS):
            features.recent_greeting_used = True
            break
    if any(phrase in last_text_lower for phrase in DISCLOSURE_KEYWORDS): features.disclosure = True
    if last_turn.role == 'user' and '?' in last_text_lower: features.question_asking = True
    match_turns = [t for t in turns if t.role == 'match']
    if match_turns and '?' in match_turns[-1].text: features.match_contains_question = True
    if len(turns) >= 2 and turns[-1].role == 'match' and turns[-2].role == 'user':
        if '?' in turns[-2].text and '?' not in turns[-1].text: features.reciprocity = True
    if len(last_turn.text) > 100: features.response_length_class = "high"
    elif len(last_turn.text) < 20: features.response_length_class = "low"
    else: features.response_length_class = "medium"

    # 2. Store the newly computed result in the cache before returning.
    probe_cache[cache_key] = features
    return features
