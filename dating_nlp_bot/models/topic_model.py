from sentence_transformers import SentenceTransformer

model_cache = {}

def get_topic_model(model_name="all-MiniLM-L6-v2"):
    """
    Loads a pre-trained sentence transformer model for embeddings.
    Caches the model after first load.
    """
    if model_name in model_cache:
        return model_cache[model_name]

    try:
        model = SentenceTransformer(model_name)
        model_cache[model_name] = model
        return model
    except Exception as e:
        print(f"Error loading topic model '{model_name}': {e}")
        # This could be due to network issues or an invalid model name
        return None
