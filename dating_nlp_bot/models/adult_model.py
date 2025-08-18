from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

model_cache = {}

def get_adult_content_model(model_name="unitary/toxic-bert"):
    """
    Loads a pre-trained model for detecting toxic/adult content.
    Caches the model after first load.
    """
    if model_name in model_cache:
        return model_cache[model_name]

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        adult_content_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer, return_all_scores=True)

        model_cache[model_name] = adult_content_pipeline
        return adult_content_pipeline
    except Exception as e:
        print(f"Error loading adult content model '{model_name}': {e}")
        return None
