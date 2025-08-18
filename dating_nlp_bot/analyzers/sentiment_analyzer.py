from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from ..models.sentiment_model import get_sentiment_model

def analyze_sentiment_fast(conversation_history):
    """
    Analyzes sentiment for each message in the conversation history using VADER.
    """
    analyzer = SentimentIntensityAnalyzer()
    per_message_sentiments = []
    overall_scores = []

    for message in conversation_history:
        vs = analyzer.polarity_scores(message['content'])
        compound_score = vs['compound']
        overall_scores.append(compound_score)

        if compound_score >= 0.05:
            per_message_sentiments.append("positive")
        elif compound_score <= -0.05:
            per_message_sentiments.append("negative")
        else:
            per_message_sentiments.append("neutral")

    overall_sentiment_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0

    if overall_sentiment_score >= 0.05:
        overall_sentiment = "positive"
    elif overall_sentiment_score <= -0.05:
        overall_sentiment = "negative"
    else:
        overall_sentiment = "neutral"

    return {
        "per_message": per_message_sentiments,
        "overall": overall_sentiment,
        "confidence": 0.8 # VADER is rule-based, so confidence is heuristic
    }

def analyze_sentiment_enhanced(conversation_history, model_name=None):
    """
    Analyzes sentiment using a transformer model.
    """
    model = get_sentiment_model(model_name if model_name else "cardiffnlp/twitter-roberta-base-sentiment")
    if not model:
        return analyze_sentiment_fast(conversation_history) # Fallback to fast mode

    per_message_sentiments = []
    confidences = []

    for message in conversation_history:
        try:
            result = model(message['content'])[0]
            label = result['label'].lower()

            if "positive" in label:
                per_message_sentiments.append("positive")
            elif "negative" in label:
                per_message_sentiments.append("negative")
            else:
                per_message_sentiments.append("neutral")
            confidences.append(result['score'])
        except Exception:
            per_message_sentiments.append("neutral")
            confidences.append(0.0)

    overall = max(set(per_message_sentiments), key=per_message_sentiments.count) if per_message_sentiments else "neutral"

    return {
        "per_message": per_message_sentiments,
        "overall": overall,
        "confidence": sum(confidences) / len(confidences) if confidences else 0.0
    }

def analyze_sentiment(conversation_history, use_enhanced_nlp, model_name=None):
    if use_enhanced_nlp:
        return analyze_sentiment_enhanced(conversation_history, model_name)
    else:
        return analyze_sentiment_fast(conversation_history)
