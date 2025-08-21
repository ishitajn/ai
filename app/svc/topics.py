from collections import Counter
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Tuple
from app.schemas import Message, Topic
import asyncio

# Basic stop words list, expanded for chat context
STOP_WORDS = {
    'a', 'an', 'the', 'in', 'on', 'at', 'for', 'to', 'of', 'is', 'are', 'was', 'were',
    'and', 'but', 'or', 'so', 'if', 'it', 'i', 'you', 'he', 'she', 'we', 'they', 'im',
    'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'mine',
    'what', 'who', 'when', 'where', 'why', 'how', 'do', 'does', 'did', 'be', 'lol',
    'will', 'can', 'should', 'would', 'could', 'not', 'no', 'very', 'just', 'like', 'u'
}

# Keywords for categorization
SEXUAL_KEYWORDS = {"sex", "fuck", "kink", "fetish", "bdsm", "porn", "horny"}
SENSITIVE_KEYWORDS = {"politics", "religion", "money", "finance", "ex", "grief", "death"}

def _get_topic_details(messages: List[str], all_turns: List[Message]) -> Tuple[str, List[str], str]:
    """Generates a label, keywords, and a category for a cluster of messages."""
    if not messages:
        return "Unknown", [], "neutral"

    # 1. Extract keywords from the messages in the cluster
    word_counts = Counter()
    for msg in messages:
        words = msg.lower().split()
        for word in words:
            cleaned_word = ''.join(filter(str.isalnum, word))
            if cleaned_word and cleaned_word not in STOP_WORDS:
                word_counts[cleaned_word] += 1

    if not word_counts:
        return "General Chat", [], "neutral"

    keywords = [word for word, count in word_counts.most_common(3)]
    label = keywords[0].capitalize() if keywords else "General Chat"

    # 2. Categorize the topic based on keywords and context
    category = "neutral"
    lower_keywords = {k.lower() for k in keywords}

    if any(k in SEXUAL_KEYWORDS for k in lower_keywords):
        category = "sexual"
    elif any(k in SENSITIVE_KEYWORDS for k in lower_keywords):
        category = "sensitive"

    # Check if this topic is a "focus" topic (related to a recent question from the user)
    if len(all_turns) > 0:
        last_turn = all_turns[-1]
        if last_turn.role == 'user' and '?' in last_turn.text:
            if any(k in last_turn.text.lower() for k in lower_keywords):
                category = "focus"

    return label, keywords, category

async def assign(turns: List[Message], vecs: np.ndarray) -> List[Topic]:
    """
    Assigns categorized topics to the conversation turns using embedding clustering.
    Made async to run concurrently.
    """
    await asyncio.sleep(0)

    if vecs.shape[0] < 3:
        return [Topic(label="Opening Chat", keywords=["greeting"], category="neutral")]

    n_clusters = max(2, min(len(turns) // 3, 5))

    # n_init=1 is used for performance, as we don't need perfect clusters for this mock.
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=1)
    try:
        vecs_float32 = vecs.astype(np.float32)
        kmeans.fit(vecs_float32)
    except Exception as e:
        print(f"Error during clustering: {e}")
        return [Topic(label="General Discussion", keywords=[], category="neutral")]

    labels = kmeans.labels_

    # Group messages by cluster
    clusters: List[List[str]] = [[] for _ in range(n_clusters)]
    for i, turn in enumerate(turns):
        clusters[labels[i]].append(turn.text)

    # Create categorized Topic objects
    topics: List[Topic] = []
    unique_labels = set()
    for i in range(n_clusters):
        if clusters[i]:
            label, keywords, category = _get_topic_details(clusters[i], turns)
            if label not in unique_labels:
                topics.append(Topic(label=label, keywords=keywords, category=category))
                unique_labels.add(label)

    return topics
