import re
from ..utils.text_preprocessing import preprocess_text
from ..models.topic_model import get_topic_model
from sklearn.cluster import KMeans
import numpy as np

# A simple keyword-based topic classifier for the fast mode
TOPIC_KEYWORDS = {
    "travel": ["trip", "vacation", "fly", "tour", "explore"],
    "food": ["coffee", "breakfast", "lunch", "dinner", "eat", "restaurant"],
    "flirt": ["charm", "cute", "handsome", "beautiful", "sexy"],
    "sexual": ["kiss", "smooch", "bed", "naked"],
    "sports": ["jogging", "gym", "workout", "football", "basketball"],
    "career": ["job", "work", "office", "company", "career"],
    "family": ["niece", "kids", "mom", "dad", "family", "parents"],
    "fashion_beauty": ["style", "clothes", "dress", "makeup", "hair"],
    "relationships": ["date", "dating", "relationship", "partner"],
    "self_care": ["workout", "meditation", "spa", "relax"],
    "emotions": ["positivity", "kindness", "happy", "sad", "love"],
    "social_life": ["friend", "party", "bar", "club"]
}

def classify_topics_fast(conversation_history):
    """
    Classifies topics based on keyword matching.
    """
    liked = []
    disliked = []
    neutral = []
    heatmap = {key: [] for key in TOPIC_KEYWORDS.keys()}

    full_text = " ".join([msg['content'] for msg in conversation_history])
    processed_text = preprocess_text(full_text)

    for topic, keywords in TOPIC_KEYWORDS.items():
        found_keywords = [kw for kw in keywords if re.search(r'\b' + kw + r'\b', processed_text)]
        if found_keywords:
            neutral.append(topic)
            heatmap[topic].extend(found_keywords)

    return {
      "liked": [], "disliked": [], "neutral": neutral,
      "heatmap": {
        "travel": heatmap["travel"], "food": heatmap["food"], "flirt": heatmap["flirt"],
        "sexual": heatmap["sexual"], "sports": heatmap["sports"], "career": heatmap["career"],
        "female_centric": {
          "family": heatmap["family"], "fashion_beauty": heatmap["fashion_beauty"],
          "relationships": heatmap["relationships"], "self_care": heatmap["self_care"],
          "emotions": heatmap["emotions"], "social_life": heatmap["social_life"]
        }
      },
      "sensitive": [], "kinksAndFetishes": [], "pornReferences": []
    }

def classify_topics_enhanced(conversation_history, model_name=None):
    """
    Classifies topics using sentence embeddings and clustering.
    """
    model = get_topic_model(model_name if model_name else "all-MiniLM-L6-v2")
    if not model:
        return classify_topics_fast(conversation_history)

    full_text = ". ".join([msg['content'] for msg in conversation_history])
    sentences = [s.strip() for s in full_text.split('.') if s.strip()]

    if not sentences:
        return {"liked": [], "disliked": [], "neutral": [], "heatmap": {}, "sensitive": [], "kinksAndFetishes": [], "pornReferences": []}

    embeddings = model.encode(sentences)

    num_clusters = min(5, len(sentences))
    if num_clusters == 0:
        return {"liked": [], "disliked": [], "neutral": [], "heatmap": {}, "sensitive": [], "kinksAndFetishes": [], "pornReferences": []}

    kmeans = KMeans(n_clusters=num_clusters, random_state=0, n_init='auto')
    kmeans.fit(embeddings)

    # This is a placeholder; a real implementation would map cluster centroids to topic labels.
    identified_topics = [f"topic_{i+1}" for i in range(num_clusters)]

    return {
      "liked": [], "disliked": [], "neutral": identified_topics, "heatmap": {},
      "sensitive": [], "kinksAndFetishes": [], "pornReferences": []
    }

def classify_topics(conversation_history, use_enhanced_nlp, model_name=None):
    if use_enhanced_nlp:
        return classify_topics_enhanced(conversation_history, model_name)
    else:
        return classify_topics_fast(conversation_history)
