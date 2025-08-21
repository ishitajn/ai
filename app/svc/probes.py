from typing import List
from app.schemas import Message, FeatureProbes
import numpy as np

# Simple keyword-based detectors
GREETING_KEYWORDS = {"hello", "hi", "hey", "yo"}
FLIRT_KEYWORDS = {"wink", "cute", "crush", ";)", ":-)"}
QUESTION_WORDS = {"?", "what", "who", "when", "where", "why", "how"}
DISCLOSURE_KEYWORDS = {"i think", "i feel", "my favorite", "i love"}

def evaluate(turns: List[Message], vecs: np.ndarray) -> FeatureProbes:
    """
    Computes booleans and flags based on conversation turns.
    This is a simplified rule-based implementation.
    """
    features = FeatureProbes()
    if not turns:
        return features

    last_turn = turns[-1]
    last_text_lower = last_turn.text.lower()

    # --- Basic Probes on the last turn ---
    if any(word in last_text_lower for word in GREETING_KEYWORDS):
        features.greetings = True

    if '?' in last_text_lower:
        features.questions = True

    if any(word in last_text_lower for word in FLIRT_KEYWORDS):
        features.flirtation_detected = True
        features.playful_energy = True # Assume flirtation is playful

    # --- Engagement Signals ---
    # Disclosure: Does the last turn contain self-revealing statements?
    if any(phrase in last_text_lower for phrase in DISCLOSURE_KEYWORDS):
        features.disclosure = True

    # Question Asking: Is the user asking questions? (based on last turn)
    if last_turn.role == 'user' and '?' in last_text_lower:
        features.question_asking = True

    # Reciprocity: Did the match answer a question from the user? (Simple version)
    if len(turns) >= 2:
        second_last_turn = turns[-2]
        # Check if user asked and match responded without a question
        if '?' in second_last_turn.text and second_last_turn.role == 'user':
            if '?' not in last_turn.text and last_turn.role == 'match':
                features.reciprocity = True

    # Response Length
    if len(last_turn.text) > 100:
        features.response_length_class = "high"
    elif len(last_turn.text) < 20:
        features.response_length_class = "low"
    else:
        features.response_length_class = "medium"

    return features
