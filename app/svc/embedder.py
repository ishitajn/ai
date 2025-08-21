from typing import List, Dict
import numpy as np

# In-memory cache for embeddings
embedding_cache: Dict[str, np.ndarray] = {}

def encode_cached(texts: List[str]) -> np.ndarray:
    """
    Generates int8 embeddings for a list of texts, using a cache.
    This is a mock implementation that simulates embedding generation.
    """
    embeddings = []
    max_len = 0

    # Pre-calculate max_len based on all texts to ensure uniform shape
    for text in texts:
        max_len = max(max_len, len(text))

    # Process texts
    for text in texts:
        if text in embedding_cache:
            # Use cached embedding
            embedding = embedding_cache[text]
        else:
            # Simple embedding: ASCII values of characters
            embedding = np.array([ord(c) for c in text], dtype=np.int8)
            embedding_cache[text] = embedding # Update cache

        # Pad to max_len for this batch
        padded_embedding = np.zeros(max_len, dtype=np.int8)
        padded_embedding[:len(embedding)] = embedding
        embeddings.append(padded_embedding)

    if not embeddings:
        return np.array([])

    return np.vstack(embeddings)
