from collections import Counter
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Tuple
from app.schemas import Message, Topic

# Basic stop words list, expanded for chat context
STOP_WORDS = {
    'a', 'an', 'the', 'in', 'on', 'at', 'for', 'to', 'of', 'is', 'are', 'was', 'were',
    'and', 'but', 'or', 'so', 'if', 'it', 'i', 'you', 'he', 'she', 'we', 'they', 'im',
    'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'mine',
    'what', 'who', 'when', 'where', 'why', 'how', 'do', 'does', 'did', 'be', 'lol',
    'will', 'can', 'should', 'would', 'could', 'not', 'no', 'very', 'just', 'like', 'u'
}

def _get_cluster_label(messages: List[str]) -> Tuple[str, List[str]]:
    """Generates a label and keywords for a cluster of messages."""
    if not messages:
        return "Unknown Topic", []

    word_counts = Counter()
    for msg in messages:
        words = msg.lower().split()
        for word in words:
            cleaned_word = ''.join(filter(str.isalnum, word))
            if cleaned_word and cleaned_word not in STOP_WORDS:
                word_counts[cleaned_word] += 1

    if not word_counts:
        return "General Chat", []

    keywords = [word for word, count in word_counts.most_common(3)]
    label = keywords[0] if keywords else "General Chat"

    return label.capitalize(), keywords


def assign(turns: List[Message], vecs: np.ndarray) -> List[Topic]:
    """
    Assigns topics to the conversation turns using embedding clustering.
    """
    if vecs.shape[0] < 3:
        return [Topic(label="Opening Chat", keywords=["greeting"])]

    # Determine the number of clusters (topics)
    n_clusters = max(2, min(len(turns) // 3, 5))

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    try:
        # Ensure vectors are float32 for KMeans
        vecs_float32 = vecs.astype(np.float32)
        kmeans.fit(vecs_float32)
    except Exception as e:
        print(f"Error during clustering: {e}")
        return [Topic(label="General Discussion", keywords=[])]

    labels = kmeans.labels_

    clusters: List[List[str]] = [[] for _ in range(n_clusters)]
    for i, turn in enumerate(turns):
        clusters[labels[i]].append(turn.text)

    topics: List[Topic] = []
    unique_labels = set()
    for i in range(n_clusters):
        if clusters[i]:
            label, keywords = _get_cluster_label(clusters[i])
            if label not in unique_labels:
                topics.append(Topic(label=label, keywords=keywords))
                unique_labels.add(label)

    return topics
