import json
from .analyzers.sentiment_analyzer import analyze_sentiment
from .analyzers.topic_classifier import classify_topics
from .analyzers.adult_content import analyze_adult_content
from .analyzers.conversation_dynamics import analyze_conversation_dynamics
from .analyzers.geo_time_analyzer import analyze_geo_time
from .analyzers.response_analysis import analyze_response
from .recommender.topic_suggester import suggest_topics
from .recommender.action_recommender import recommend_actions

def run_fast_pipeline(payload):
    """Runs the fast analysis pipeline."""
    conversation_history = payload["scraped_data"]["conversationHistory"]

    sentiment = analyze_sentiment(conversation_history, use_enhanced_nlp=False)
    topics = classify_topics(conversation_history, use_enhanced_nlp=False)
    adult_content = analyze_adult_content(conversation_history, use_enhanced_nlp=False)
    topics.update(adult_content) # Combine adult content into topics

    dynamics = analyze_conversation_dynamics(conversation_history, use_enhanced_nlp=False)
    geo_time = analyze_geo_time(payload["ui_settings"]["myLocation"], payload["scraped_data"]["theirLocationString"])
    response = analyze_response(conversation_history)

    suggested_topics = suggest_topics(topics)

    results = {
        "sentiment": sentiment,
        "topics": topics,
        "conversation_dynamics": dynamics,
        "geoContext": geo_time,
        "response_analysis": response,
        "suggested_topics": suggested_topics
    }

    recommended_actions = recommend_actions(results)
    results["recommended_actions"] = recommended_actions

    return results

def run_enhanced_pipeline(payload):
    """Runs the enhanced analysis pipeline."""
    conversation_history = payload["scraped_data"]["conversationHistory"]
    model_name = payload["ui_settings"].get("local_model_name")

    sentiment = analyze_sentiment(conversation_history, use_enhanced_nlp=True, model_name=model_name)
    topics = classify_topics(conversation_history, use_enhanced_nlp=True, model_name=model_name)
    adult_content = analyze_adult_content(conversation_history, use_enhanced_nlp=True, model_name=model_name)
    topics.update(adult_content)

    dynamics = analyze_conversation_dynamics(conversation_history, use_enhanced_nlp=True, model_name=model_name)
    geo_time = analyze_geo_time(payload["ui_settings"]["myLocation"], payload["scraped_data"]["theirLocationString"])
    response = analyze_response(conversation_history)

    suggested_topics = suggest_topics(topics)

    results = {
        "sentiment": sentiment,
        "topics": topics,
        "conversation_dynamics": dynamics,
        "geoContext": geo_time,
        "response_analysis": response,
        "suggested_topics": suggested_topics
    }

    recommended_actions = recommend_actions(results)
    results["recommended_actions"] = recommended_actions

    return results

def handler(payload):
    """
    Main handler function that processes the input payload.
    """
    if not isinstance(payload, dict):
        payload = json.loads(payload)

    use_enhanced_nlp = payload.get("ui_settings", {}).get("useEnhancedNlp", False)

    if use_enhanced_nlp:
        final_output = run_enhanced_pipeline(payload)
    else:
        final_output = run_fast_pipeline(payload)

    return final_output

if __name__ == '__main__':
    # Example payload for testing
    example_payload = {
      "matchId": "unique_match_id_123",
      "scraped_data": {
        "myName": "Alex",
        "theirName": "Jess",
        "theirProfile": "Lover of dogs, coffee, and good conversation.",
        "theirLocationString": "New York, USA",
        "conversationHistory": [
          {
            "role": "user",
            "content": "Hey, how's your week going?",
            "date": "2023-10-26"
          },
          {
            "role": "assistant",
            "content": "It's been great! Just got back from a hike.",
            "date": "2023-10-26"
          }
        ]
      },
      "ui_settings": {
        "useEnhancedNlp": False,
        "myLocation": "Brooklyn, New York, USA",
        "myProfile": "Software engineer, enjoys travel and photography.",
        "local_model_name": None
      }
    }

    # To run this, you would need to have all the dependencies installed
    # and the other modules created. This is just for structure.
    # analysis_results = handler(example_payload)
    # print(json.dumps(analysis_results, indent=2))
    print("main.py created. Run this file to test the full pipeline once all modules are implemented.")
