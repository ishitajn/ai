import faiss
import numpy as np
from typing import List, Set, Tuple
from app.schemas import Message

# In-memory FAISS index and tracking for added items
_index = None
_dimension = 0
_added_ids: Set[str] = set()

def _initialize_index(dim: int):
    """Initializes the FAISS index."""
    global _index, _dimension
    _dimension = dim
    # Using HNSW for the index as specified. This is a good choice for speed.
    # The index is wrapped in an IndexIDMap to allow for custom (non-contiguous) IDs.
    hnsw_index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_L2)
    _index = faiss.IndexIDMap(hnsw_index)

def ensure_added(turns: List[Message], vecs: np.ndarray):
    """
    Ensures that new turns are added to the FAISS index.
    A simple implementation using message timestamps as unique IDs.
    """
    global _index, _added_ids

    if vecs.shape[0] == 0:
        return  # Nothing to add

    if _index is None:
        _initialize_index(vecs.shape[1])

    # In our mock setup, vector dimensions can change. In prod, they are fixed.
    # This is a safeguard for the mock implementation.
    if vecs.shape[1] != _dimension:
        print(f"Warning: Vector dimension changed from {_dimension} to {vecs.shape[1]}. Re-initializing index.")
        _initialize_index(vecs.shape[1])
        _added_ids.clear()

    ids_to_add = []
    vecs_to_add = []

    for i, turn in enumerate(turns):
        turn_id = turn.timestamp
        if turn_id not in _added_ids:
            # We need a numerical id for FAISS IndexIDMap.
            # hash() is not stable across processes, but fine for this single-run script.
            # A more robust solution would use a proper hashing function like murmurhash.
            numerical_id = abs(hash(turn_id)) % (2**63) # Ensure positive 64-bit int
            ids_to_add.append(numerical_id)
            vecs_to_add.append(vecs[i])
            _added_ids.add(turn_id)

    if vecs_to_add:
        vecs_to_add_np = np.array(vecs_to_add, dtype=np.float32)
        ids_to_add_np = np.array(ids_to_add, dtype=np.int64)

        # HNSW does not require training, but the API is there.
        if not _index.is_trained:
            _index.train(vecs_to_add_np)

        _index.add_with_ids(vecs_to_add_np, ids_to_add_np)

def search(query_vec: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Performs a similarity search on the index.
    Returns distances and IDs.
    """
    if _index is None or _index.ntotal == 0:
        return np.array([]), np.array([])

    # Ensure query vector is float32 and 2D
    query_vec = query_vec.astype(np.float32).reshape(1, -1)

    # Pad if necessary to match index dimension
    if query_vec.shape[1] < _dimension:
        padded_query = np.zeros((1, _dimension), dtype=np.float32)
        padded_query[0, :query_vec.shape[1]] = query_vec
        query_vec = padded_query
    elif query_vec.shape[1] > _dimension:
        query_vec = query_vec[:, :_dimension]

    distances, ids = _index.search(query_vec, k)
    return distances, ids
