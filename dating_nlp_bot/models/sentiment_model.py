from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Global cache for models to avoid reloading them on every call
model_cache = {}

def get_sentiment_model(model_name="cardiffnlp/twitter-roberta-base-sentiment"):
    """
    Loads a pre-trained sentiment analysis model from Hugging Face.
    Caches the model after first load to improve performance.
    """
    if model_name in model_cache:
        return model_cache[model_name]

    try:
        # Ensure tokenizer and model are loaded with explicit references
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

        model_cache[model_name] = sentiment_pipeline
        return sentiment_pipeline
    except Exception as e:
        print(f"Error loading sentiment model '{model_name}': {e}")
        # This can happen if the model is not found or there's a network issue
        return None
