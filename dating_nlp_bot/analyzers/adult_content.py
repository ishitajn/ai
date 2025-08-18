import re
from ..utils.text_preprocessing import preprocess_text
from ..models.adult_model import get_adult_content_model

SENSITIVE_KEYWORDS = {
    "flirty": ["flirt", "crush", "date", "cute", "handsome", "beautiful", "sexy"],
    "sexual": ["sex", "sexual", "intimate", "kiss", "bed", "naked"],
    "kinksAndFetishes": ["bdsm", "roleplay", "dom", "sub", "fetish", "kink"],
    "pornReferences": ["porn", "onlyfans", "xvideos", "pornhub"]
}

def analyze_adult_content_fast(conversation_history):
    """
    Analyzes for adult content using keyword matching.
    """
    sensitive_topics = []
    kinks = []
    porn_refs = []

    full_text = " ".join([msg['content'] for msg in conversation_history])
    processed_text = preprocess_text(full_text)

    if any(re.search(r'\b' + keyword + r'\b', processed_text) for keyword in SENSITIVE_KEYWORDS['flirty']):
        sensitive_topics.append("flirty")
    if any(re.search(r'\b' + keyword + r'\b', processed_text) for keyword in SENSITIVE_KEYWORDS['sexual']):
        sensitive_topics.append("sexual")

    found_kinks = [kw for kw in SENSITIVE_KEYWORDS['kinksAndFetishes'] if re.search(r'\b' + kw + r'\b', processed_text)]
    if found_kinks:
        kinks.extend(found_kinks)

    found_porn_refs = [kw for kw in SENSITIVE_KEYWORDS['pornReferences'] if re.search(r'\b' + kw + r'\b', processed_text)]
    if found_porn_refs:
        porn_refs.append("video mention") # Generic mention

    return {
        "sensitive": sensitive_topics,
        "kinksAndFetishes": kinks,
        "pornReferences": porn_refs
    }

def analyze_adult_content_enhanced(conversation_history, model_name=None):
    """
    Analyzes for adult content using a transformer model.
    """
    model = get_adult_content_model(model_name if model_name else "unitary/toxic-bert")
    if not model:
        return analyze_adult_content_fast(conversation_history)

    sensitive_topics = []

    for message in conversation_history:
        try:
            results = model(message['content'])
            for result in results:
                # This model is for toxicity, but we can adapt it
                if result['label'] in ['toxic', 'severe_toxic', 'obscene', 'sexual_explicit'] and result['score'] > 0.6:
                    if 'sexual' not in sensitive_topics:
                        sensitive_topics.append('sexual')
        except Exception:
            pass # Ignore errors on a per-message basis

    # The toxic model doesn't explicitly detect kinks or porn references, so we fall back to keyword search for those
    fast_results = analyze_adult_content_fast(conversation_history)

    return {
        "sensitive": list(set(sensitive_topics + fast_results['sensitive'])),
        "kinksAndFetishes": fast_results['kinksAndFetishes'],
        "pornReferences": fast_results['pornReferences']
    }

def analyze_adult_content(conversation_history, use_enhanced_nlp, model_name=None):
    if use_enhanced_nlp:
        return analyze_adult_content_enhanced(conversation_history, model_name)
    else:
        return analyze_adult_content_fast(conversation_history)
