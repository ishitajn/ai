def recommend_actions(analysis_results):
    """
    Recommends UI settings and actions based on the full analysis.
    This is a rule-based recommender.
    """
    dynamics = analysis_results.get("conversation_dynamics", {})
    response_analysis = analysis_results.get("response_analysis", {})
    topics = analysis_results.get("topics", {})

    # Default recommendations
    ask_question_back = True
    escalate_flirtation = False
    suggested_next_action = "BUILD_RAPPORT"
    focus_topic = "shared interests"

    # If the match just asked a question, we don't need to force another one
    if response_analysis.get("last_match_response", {}).get("contains_question"):
        ask_question_back = False

    # If the conversation is heating up, recommend escalating
    if dynamics.get("flirtation_level") in ["medium", "high"] or "sexual" in topics.get("sensitive", []):
        escalate_flirtation = True
        suggested_next_action = "ESCALATE"
        focus_topic = "sexual"

    # If the conversation is stalling, suggest a bold move
    if dynamics.get("stage") in ["break_2_days", "break_1_week"]:
        suggested_next_action = "REENGAGE"
        ask_question_back = True

    return {
        "focus_topic": focus_topic,
        "ask_question_back": ask_question_back,
        "escalate_flirtation": escalate_flirtation,
        "avoid_repeating_user": False,
        "length": 80,  # Suggest a slightly longer response
        "tone": 70,   # A generally positive tone
        "linguisticStyle": "casual",
        "emojiStrategy": "auto",
        "endWithQuestion": ask_question_back,
        "suggestedNextAction": suggested_next_action,
        "sexualCommunicationStyle": "direct_and_explicit" if escalate_flirtation else "subtle_and_suggestive",
        "dateArcPhase": "escalation" if dynamics.get("pace") == "fast" else "discovery",
        "suggestedResponseStyle": "direct"
    }
