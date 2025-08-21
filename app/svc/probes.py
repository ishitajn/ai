from typing import List
from app.schemas import Message, FeatureProbes
import numpy as np

# Keyword lists for various detectors
GREETING_KEYWORDS = {"hello", "hi", "hey", "yo", "sup"}
FLIRT_KEYWORDS = {"wink", "cute", "crush", ";)", ":-)", "beautiful"}
DISCLOSURE_KEYWORDS = {"i think", "i feel", "my favorite", "i love", "i am"}
LOCATION_KEYWORDS = {"here", "there", "place", "city", "country", "home", "area"}

def evaluate(turns: List[Message], vecs: np.ndarray) -> FeatureProbes:
    """
    Computes a wide range of booleans and flags from conversation turns
    to be used as raw signals for the final analysis.
    """
    features = FeatureProbes()
    if not turns:
        return features

    last_turn = turns[-1]
    last_text_lower = last_turn.text.lower()

    # --- Basic Probes on the last turn ---
    features.last_response_by = last_turn.role

    if any(word in last_text_lower for word in GREETING_KEYWORDS):
        features.greetings = True

    if '?' in last_text_lower:
        features.questions = True

    if any(word in last_text_lower for word in FLIRT_KEYWORDS):
        features.flirtation_detected = True
        features.playful_energy = True

    if any(word in last_text_lower for word in LOCATION_KEYWORDS):
        features.location_related = True

    # --- Contextual Probes (looking at last few turns) ---
    # Recent Greeting: Check last 3 turns
    for turn in turns[-3:]:
        if any(word in turn.text.lower() for word in GREETING_KEYWORDS):
            features.recent_greeting_used = True
            break

    # --- Engagement Signals ---
    if any(phrase in last_text_lower for phrase in DISCLOSURE_KEYWORDS):
        features.disclosure = True

    if last_turn.role == 'user' and '?' in last_text_lower:
        features.question_asking = True

    # Check if the match's last response contained a question
    match_turns = [t for t in turns if t.role == 'match']
    if match_turns:
        last_match_turn = match_turns[-1]
        if '?' in last_match_turn.text:
            features.match_contains_question = True

    # Reciprocity: Did the match answer a question from the user?
    if len(turns) >= 2 and turns[-1].role == 'match' and turns[-2].role == 'user':
        user_turn = turns[-2]
        match_turn = turns[-1]
        if '?' in user_turn.text and '?' not in match_turn.text:
            features.reciprocity = True

    # Response Length of the last message
    if len(last_turn.text) > 100:
        features.response_length_class = "high"
    elif len(last_turn.text) < 20:
        features.response_length_class = "low"
    else:
        features.response_length_class = "medium"

    return features
