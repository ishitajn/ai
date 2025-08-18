from .topic_model import get_topic_model

def generate_embeddings(text, model):
    """
    Generates sentence embeddings for a given text using a pre-loaded model.
    """
    if not model or not text:
        return None

    try:
        # The model from sentence-transformers can take a single string or a list of strings
        embeddings = model.encode(text)
        return embeddings
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return None
