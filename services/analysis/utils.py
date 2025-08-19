import logging
from typing import Dict, List

from sentence_transformers import SentenceTransformer, util
from spacy.lang.en.stop_words import STOP_WORDS

from constants import TOPIC_DEFINITIONS, INTENT_DEFINITIONS

logger = logging.getLogger(__name__)

# --- Model Loading ---
logger.info("Loading SentenceTransformer model for utils...")
model = SentenceTransformer('all-MiniLM-L6-v2')
logger.info("SentenceTransformer model loaded successfully.")

# --- Keyword Set ---
BASIC_TOPIC_KEYWORDS = {
    topic: set(word for phrase in phrases for word in phrase.split() if word not in STOP_WORDS and len(word) > 2)
    for topic, phrases in TOPIC_DEFINITIONS.items()
}

# --- Helper Functions ---
def get_semantic_scores(text: str, definitions: Dict[str, List[str]]) -> Dict[str, float]:
    """Calculates semantic similarity scores between a text and defined categories."""
    if not text:
        return {key: 0.0 for key in definitions.keys()}

    text_embedding = model.encode(text, convert_to_tensor=True)
    scores = {}

    for key, examples in definitions.items():
        example_embeddings = model.encode(examples, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(text_embedding, example_embeddings)
        scores[key] = cosine_scores.max().item()

    return scores

def score_to_heatmap(score: float) -> str:
    # This will need the constants. I'll add them to the import.
    from constants import SEMANTIC_HEATMAP_HOT_THRESHOLD, SEMANTIC_HEATMAP_MEDIUM_THRESHOLD
    if score > SEMANTIC_HEATMAP_HOT_THRESHOLD: return "hot"
    if score > SEMANTIC_HEATMAP_MEDIUM_THRESHOLD: return "medium"
    return "low"

def get_dominant_topic(text: str, use_enhanced_nlp: bool) -> str:
    """Determines the dominant topic for a given text, respecting the NLP level."""
    if not text:
        return "general"

    if use_enhanced_nlp:
        topic_scores = get_semantic_scores(text, TOPIC_DEFINITIONS)
        return max(topic_scores, key=topic_scores.get) if topic_scores else "general"
    else:
        text_words = set(text.lower().split())
        topic_scores = {
            topic: sum(1 for keyword in keywords if keyword in text_words)
            for topic, keywords in BASIC_TOPIC_KEYWORDS.items()
        }
        return max(topic_scores, key=topic_scores.get) if any(topic_scores.values()) else "general"
